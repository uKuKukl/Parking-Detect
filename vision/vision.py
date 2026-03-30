import os
import argparse
import numpy as np
import json
import sys
import cv2
import requests
from datetime import datetime
from ultralytics import YOLO

# ================= 配置区域 =================
MODEL_PATH = "models/best.pt"  # 修改为自建模型的默认存放路径
CAMERA_ID = "CAM_SOUTH_GATE_01"
LOCATION_STR = "南门自行车停放区西侧"
API_URL = "http://127.0.0.1:8080/api/violations/upload"
CONFIDENCE_THRESHOLD = 0.3
# 删除特定类别限制，让模型输出它学过的所有种类的物体！
# 这能防止模型把旁边的车识别成了类别 1（比如电动车）结果被您以前写死的类别 0 过滤掉！
TARGET_CLASSES = None 

# [新增配置: 合法停车区域]
# 运行 draw_roi.py 划定“可以停车”的绿线范围，此范围外的车将被抓拍为违停！
# 将最后打印的列表粘贴到这里。例如: LEGAL_PARKING_ZONE = [(100, 200), (300, 500)...]
# 若为 None，则表示全图禁停（只要测出车就全部算违停）。
LEGAL_PARKING_ZONE = None
ROI_REFERENCE_SIZE = None

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

# ================= 业务逻辑 =================

def main():
    parser = argparse.ArgumentParser(description="YOLO违规停车检测")
    parser.add_argument("--source", type=str, default="test_image.jpg", help="图片路径或摄像头索引(如 0)")
    parser.add_argument("--roi", type=str, default="", help="Dynamic ROI JSON array from backend")
    args = parser.parse_args()
    
    global LEGAL_PARKING_ZONE, ROI_REFERENCE_SIZE
    if args.roi:
        try:
            roi_payload = json.loads(args.roi)
            if isinstance(roi_payload, dict):
                LEGAL_PARKING_ZONE = roi_payload.get("points")
                width = roi_payload.get("referenceWidth")
                height = roi_payload.get("referenceHeight")
                if width and height:
                    ROI_REFERENCE_SIZE = (int(width), int(height))
            else:
                LEGAL_PARKING_ZONE = roi_payload
            print(f"[INFO] 成功加载动态电子围栏配置: {LEGAL_PARKING_ZONE}")
        except Exception as e:
            print(f"[ERROR] 解析动态电子围栏失败: {e}")
            sys.exit(1)
    
    test_source = args.source
    
    print(f"[INFO] 正在加载 YOLO 模型: {MODEL_PATH}")
    model = YOLO(MODEL_PATH)
    
    print(f"[INFO] 准备检测数据源: {test_source}")
    try:
        # 如果 test_image.jpg 不存在，可能报错，这里给个提示
        if isinstance(test_source, str) and not os.path.exists(test_source) and test_source != "0":
            print("[WARN] 未找到测试图片，请在 vision 目录下放置一张 test_image.jpg，或将 test_source 改为 0 使用摄像头截图一次。")
            return
            
        # 这里设置为单次推理测试，而不是连续视频流，方便触发
        results = model.predict(source=test_source, conf=CONFIDENCE_THRESHOLD, save=False, classes=TARGET_CLASSES)
        if not results:
            print("[ERROR] 未获得任何检测结果")
            sys.exit(1)
        
        for result in results:
            raw_boxes = result.boxes
            filtered_boxes = []

            roi_np = None
            if LEGAL_PARKING_ZONE:
                roi_np = np.array(LEGAL_PARKING_ZONE, dtype=np.float32)
                if ROI_REFERENCE_SIZE and len(ROI_REFERENCE_SIZE) == 2:
                    ref_width, ref_height = ROI_REFERENCE_SIZE
                    if ref_width <= 0 or ref_height <= 0:
                        print("[ERROR] ROI 参考尺寸非法")
                        sys.exit(1)
                    current_height, current_width = result.orig_img.shape[:2]
                    scale_x = current_width / ref_width
                    scale_y = current_height / ref_height
                    roi_np[:, 0] *= scale_x
                    roi_np[:, 1] *= scale_y
                roi_np = np.round(roi_np).astype(np.int32)

            # 第一步：根据防误报“合法停车区”过滤
            for box in raw_boxes:
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                cx, cy = int((x1 + x2) / 2), int(y2)  # 取车轮接地点
                
                if roi_np is not None and len(roi_np) > 2:
                    dist = cv2.pointPolygonTest(roi_np, (cx, cy), False)
                    # dist >= 0 代表车辆点在“合法停车区”内部或边界上
                    if dist >= 0:
                        continue # 因为停在了画线区域内，所以忽略它！不抓拍！
                
                # 如果代码走到这里，说明在全图禁停，或者车辆在绿线区域外部
                filtered_boxes.append(box)

            if len(filtered_boxes) > 0:
                print(f"[INFO] 检测到不在合法区域的违规车辆: {len(filtered_boxes)} 辆")
                
                max_conf_box = max(filtered_boxes, key=lambda x: x.conf[0].item())
                max_conf = max_conf_box.conf[0].item()
                obj_count = len(filtered_boxes)
                
                # 手动在一张干净的原图上画违规框和合法的绿框
                annotated_img = result.orig_img.copy()
                for box in filtered_boxes:
                    bx1, by1, bx2, by2 = map(int, box.xyxy[0].cpu().numpy())
                    conf = box.conf[0].item()
                    label = f"Violation {conf:.2f}"
                    cv2.rectangle(annotated_img, (bx1, by1), (bx2, by2), (0, 0, 255), 2)
                    cv2.putText(annotated_img, label, (bx1, by1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
                
                # 在截图里画出“允许停放区”的绿线，方便人看
                if roi_np is not None and len(roi_np) > 2:
                    cv2.polylines(annotated_img, [roi_np], isClosed=True, color=(0, 255, 0), thickness=3)

                # 保存一张总结截图
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                save_filename = f"violation_{CAMERA_ID}_{timestamp}.jpg"
                save_path = os.path.join(OUTPUT_DIR, save_filename)
                
                cv2.imwrite(save_path, annotated_img)
                print(f"[INFO] 截图已保存至: {save_path}")
                
                # 组装一条代表整个画面的汇总 JSON 数据
                payload = {
                    "detectTime": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
                    # 巧妙地利用 location 字段将数量信息传给数据库和 LLM！
                    "location": f"{LOCATION_STR} (当前画面共发现 {obj_count} 辆违停)",
                    "imagePath": save_path,
                    "cameraId": CAMERA_ID,
                    "confidence": round(max_conf, 2)
                }
                
                # 整张图片只发送一次给后端
                print(f"[INFO] 准备推送到后端: {payload}")
                try:
                    resp = requests.post(API_URL, json=payload, timeout=5)
                    if resp.status_code == 200:
                        print(f"[SUCCESS] {obj_count}辆违停的汇总数据已成功推送到后端！")
                    else:
                        print(f"[ERROR] 推送失败，HTTP 状态码: {resp.status_code}")
                        sys.exit(1)
                except Exception as e:
                    print(f"[ERROR] 连接后端失败: {e}")
                    sys.exit(1)
            else:
                print("[INFO] 当前画面虽然未检测到违规车辆，但为了人工复核，依旧将识别结果截图并上报！")
                
                annotated_img = result.orig_img.copy()
                
                # 画出绿色的允许停放区
                if roi_np is not None and len(roi_np) > 2:
                    cv2.polylines(annotated_img, [roi_np], isClosed=True, color=(0, 255, 0), thickness=3)

                # 把原本合法区域内的车用青色画出来，让人工知道 AI 是“觉得它们合法”，并不是眼瞎没看到
                for box in raw_boxes:
                    bx1, by1, bx2, by2 = map(int, box.xyxy[0].cpu().numpy())
                    cv2.rectangle(annotated_img, (bx1, by1), (bx2, by2), (255, 255, 0), 2)
                    cv2.putText(annotated_img, "Legal 1.00", (bx1, by1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)
                    
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                save_filename = f"violation_{CAMERA_ID}_OK_{timestamp}.jpg"
                save_path = os.path.join(OUTPUT_DIR, save_filename)
                
                cv2.imwrite(save_path, annotated_img)
                print(f"[INFO] 截图已保存至: {save_path}")

                payload = {
                    "detectTime": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
                    "location": f"{LOCATION_STR} (当前画面共发现 0 辆违停)",
                    "imagePath": save_path,
                    "cameraId": CAMERA_ID,
                    "confidence": 1.0 # 100%确定没有违停
                }
                
                print(f"[INFO] 准备推送 0 违规汇报到后端: {payload}")
                try:
                    resp = requests.post(API_URL, json=payload, timeout=5)
                    if resp.status_code == 200:
                        print("[SUCCESS] 0辆违停的汇总数据已成功推送到后端！")
                    else:
                        print(f"[ERROR] 推送失败，HTTP 状态码: {resp.status_code}")
                        sys.exit(1)
                except Exception as e:
                    print(f"[ERROR] 连接后端失败: {e}")
                    sys.exit(1)
                
    except Exception as e:
        print(f"[ERROR] 检测运行出错: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

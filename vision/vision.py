import cv2
import requests
import time
import os
import argparse
from datetime import datetime
from ultralytics import YOLO

# ================= 配置区域 =================
MODEL_PATH = "models/best.pt"  # 修改为自建模型的默认存放路径
CAMERA_ID = "CAM_SOUTH_GATE_01"
LOCATION_STR = "南门自行车停放区西侧"
API_URL = "http://127.0.0.1:8080/api/violations/upload"
CONFIDENCE_THRESHOLD = 0.5
# 假设自建模型训练时只标注了“违规车”一类，那 ID 通常是 0。请视实际情况修改！
TARGET_CLASSES = [0] 

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

# ================= 业务逻辑 =================

def main():
    parser = argparse.ArgumentParser(description="YOLO违规停车检测")
    parser.add_argument("--source", type=str, default="test_image.jpg", help="图片路径或摄像头索引(如 0)")
    args = parser.parse_args()
    
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
        
        for result in results:
            boxes = result.boxes
            if len(boxes) > 0:
                print(f"[INFO] 检测到违规目标数量: {len(boxes)}")
                
                # 选取画面中置信度最高的值作为参考
                max_conf_box = max(boxes, key=lambda x: x.conf[0].item())
                max_conf = max_conf_box.conf[0].item()
                obj_count = len(boxes)
                
                # 获取原图并画带有完整边界框的图像(一张图画上所有框)
                annotated_img = result.plot()
                
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
                except Exception as e:
                    print(f"[ERROR] 连接后端失败: {e}")
            else:
                print("[INFO] 当前画面未检测到目标类别的违规情况。")
                
    except Exception as e:
        print(f"[ERROR] 检测运行出错: {e}")

if __name__ == "__main__":
    main()

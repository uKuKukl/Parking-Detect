import cv2
import numpy as np
import argparse

points = []
img_copy = None

def mouse_callback(event, x, y, flags, param):
    global points, img_copy
    if event == cv2.EVENT_LBUTTONDOWN:
        points.append((x, y))
        print(f"[*] 增加点: ({x}, {y})")
    elif event == cv2.EVENT_RBUTTONDOWN:
        if points:
            removed = points.pop()
            print(f"[*] 移除上一个点: {removed}")
    
    # 重新在副本上画出所有点和线
    img_copy = img.copy()
    if len(points) > 0:
        for p in points:
            cv2.circle(img_copy, p, 5, (0, 255, 0), -1)
    if len(points) > 1:
        cv2.polylines(img_copy, [np.array(points)], isClosed=False, color=(0, 255, 0), thickness=2)
    if len(points) > 2:
        # 画出闭合的多边形边界预警虚线效果 (方便观看最终封口)
        cv2.polylines(img_copy, [np.array(points)], isClosed=True, color=(0, 255, 0), thickness=2)
        
    cv2.imshow("Draw LEGAL Parking Zone (Left: Add | Right: Undo | Enter: Finish)", img_copy)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="绘制【合法停车区】 ROI 工具")
    parser.add_argument("--source", type=str, default="test_image.jpg", help="被标记的图片路径")
    args = parser.parse_args()
    
    img = cv2.imread(args.source)
    if img is None:
        print(f"[!] 无法加载图片: {args.source}，请确保该图片存在！")
        exit(1)
        
    img_copy = img.copy()
    cv2.imshow("Draw LEGAL Parking Zone (Left: Add | Right: Undo | Enter: Finish)", img_copy)
    cv2.setMouseCallback("Draw LEGAL Parking Zone (Left: Add | Right: Undo | Enter: Finish)", mouse_callback)
    
    print("\n======= 开始绘制【合法停车区】 =======")
    print(" - 鼠标左键：落下一个顶点")
    print(" - 鼠标右键：撤销上一个点")
    print(" - 提示：请把【允许停车】的区域用绿色框包围起来！")
    print(" - 车子只要停在这个绿框外面，就会被抓拍违停！")
    print(" - 回车键（Enter）：完成绘制并生成坐标")
    print("======================================\n")
    
    while True:
        key = cv2.waitKey(1) & 0xFF
        if key == 13 or key == 27: # Enter 或 ESC 键结束
            break
            
    cv2.destroyAllWindows()
    
    if len(points) > 2:
        print("\n✅ 绘制完成！请复制下方生成的列表数组，并粘贴到 vision.py 的 LEGAL_PARKING_ZONE 变量中：\n")
        print(f"LEGAL_PARKING_ZONE = {points}\n")
    else:
        print("\n❌ 取消保存：区域必须至少三个点才能闭合构成区域哦！\n")

from ultralytics import YOLO

model = YOLO('model/best.pt')

print("🤖 MODEL INFO:")
print(f"Model: {model}")
print(f"Classes: {model.names}")
print(f"Number of classes: {len(model.names)}")

# Try to detect variant
try:
    param_count = sum(p.numel() for p in model.model.parameters())
    print(f"Parameter count: {param_count:,}")
    
    if param_count < 3_000_000:
        print("Variant: YOLOv8n (nano)")
    elif param_count < 10_000_000:
        print("Variant: YOLOv8s (small)")
    elif param_count < 25_000_000:
        print("Variant: YOLOv8m (medium)")
    elif param_count < 50_000_000:
        print("Variant: YOLOv8l (large)")
    else:
        print("Variant: YOLOv8x (extra large)")
except:
    print("Could not determine variant")
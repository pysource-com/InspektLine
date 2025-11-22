from camera.camera import Camera
import cv2
# load image classifier
from detector.classifier import TransformerImageClassifier

model = r"trainer/outputs/epoch-9"
classifier = TransformerImageClassifier(
    model_name=model,
    device="cuda",
)

camera = Camera()
cameras_list = camera.get_cameras_list()

cap = camera.load_cap(1, camera_type="intel-realsense")

# State for displaying text
show_text = False
display_text = ""
text_color = (0, 0, 0)
font = cv2.FONT_HERSHEY_SIMPLEX
position = (50, 50)
font_scale = 1.5
font_thickness = 3

while True:
    ret, frame = camera.read_frame(cap)
    if not ret:
        break

    # Make a copy of the frame to draw on
    display_frame = frame.copy()

    # Display text if enabled
    if show_text:
        cv2.putText(display_frame, display_text, position, font, font_scale, text_color, font_thickness)

    cv2.imshow("Frame", display_frame)

    key = cv2.waitKey(1) & 0xFF
    if key == 27:  # ESC key
        break
    elif key == ord("i"):
        # Identify defects
        results = classifier.predict([frame.copy()], top_k=1, return_probabilities=True)
        print("Defect Identification Results:")
        if results and results[0]:
            top_result = results[0][0]
            label = top_result['label']
            print(f"Label: {label}, Score: {top_result['score']:.4f}, ID: {top_result['id']}")

            # Assuming 'defective' is one of the possible labels
            if "defective" in label.lower():
                display_text = "Defective"
                text_color = (0, 0, 255)  # Red in BGR
            else:
                display_text = "Ok"
                text_color = (0, 255, 0)  # Green in BGR
            show_text = True

    elif key == 32:  # Backspace key
        show_text = False

camera.release_cap(cap)
cv2.destroyAllWindows()

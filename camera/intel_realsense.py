import pyrealsense2 as rs
import numpy as np
import cv2


class IntelRealSenseD435i:
    """
    Intel RealSense D435i camera class for capturing BGR and depth frames.
    """

    def __init__(self, width=640, height=480, fps=30):
        """
        Initialize the Intel RealSense D435i camera.

        Args:
            width (int): Frame width (default: 640)
            height (int): Frame height (default: 480)
            fps (int): Frames per second (default: 30)
        """
        self.width = width
        self.height = height
        self.fps = fps

        # Create pipeline and config
        self.pipeline = rs.pipeline()
        self.config = rs.config()

        # Configure streams
        self.config.enable_stream(rs.stream.color, width, height, rs.format.bgr8, fps)
        self.config.enable_stream(rs.stream.depth, width, height, rs.format.z16, fps)

        # Align object to align depth frames to color frames
        self.align = rs.align(rs.stream.color)

        # Pipeline profile (will be set when started)
        self.profile = None
        self.is_running = False

    def start(self):
        """
        Start the camera pipeline.

        Returns:
            bool: True if started successfully, False otherwise
        """
        try:
            self.profile = self.pipeline.start(self.config)
            self.is_running = True

            # Get device info
            device = self.profile.get_device()
            device_name = device.get_info(rs.camera_info.name)
            serial_number = device.get_info(rs.camera_info.serial_number)
            print(f"Started Intel RealSense camera: {device_name} (SN: {serial_number})")

            # Wait for camera to stabilize
            for _ in range(30):
                self.pipeline.wait_for_frames()

            return True
        except Exception as e:
            print(f"Failed to start Intel RealSense camera: {e}")
            self.is_running = False
            return False

    def stop(self):
        """
        Stop the camera pipeline.
        """
        if self.is_running:
            self.pipeline.stop()
            self.is_running = False
            print("Stopped Intel RealSense camera")

    def get_bgr_frame(self):
        """
        Grab a BGR color frame from the camera.

        Returns:
            numpy.ndarray: BGR image as numpy array, or None if failed
        """
        if not self.is_running:
            print("Camera is not running. Call start() first.")
            return None

        try:
            # Wait for frames
            frames = self.pipeline.wait_for_frames()

            # Align depth to color
            aligned_frames = self.align.process(frames)

            # Get color frame
            color_frame = aligned_frames.get_color_frame()

            if not color_frame:
                return None

            # Convert to numpy array
            bgr_image = np.asanyarray(color_frame.get_data())

            return bgr_image
        except Exception as e:
            print(f"Error grabbing BGR frame: {e}")
            return None

    def get_depth_frame(self):
        """
        Grab a depth frame from the camera.

        Returns:
            numpy.ndarray: Depth image as numpy array (uint16), or None if failed
        """
        if not self.is_running:
            print("Camera is not running. Call start() first.")
            return None

        try:
            # Wait for frames
            frames = self.pipeline.wait_for_frames()

            # Align depth to color
            aligned_frames = self.align.process(frames)

            # Get depth frame
            depth_frame = aligned_frames.get_depth_frame()

            if not depth_frame:
                return None

            # Convert to numpy array
            depth_image = np.asanyarray(depth_frame.get_data())

            return depth_image
        except Exception as e:
            print(f"Error grabbing depth frame: {e}")
            return None

    def get_both_frames(self):
        """
        Grab both BGR and depth frames simultaneously (more efficient than calling separately).

        Returns:
            tuple: (bgr_image, depth_image) as numpy arrays, or (None, None) if failed
        """
        if not self.is_running:
            print("Camera is not running. Call start() first.")
            return None, None

        try:
            # Wait for frames
            frames = self.pipeline.wait_for_frames()

            # Align depth to color
            aligned_frames = self.align.process(frames)

            # Get both frames
            color_frame = aligned_frames.get_color_frame()
            depth_frame = aligned_frames.get_depth_frame()

            if not color_frame or not depth_frame:
                return None, None

            # Convert to numpy arrays
            bgr_image = np.asanyarray(color_frame.get_data())
            depth_image = np.asanyarray(depth_frame.get_data())

            return bgr_image, depth_image
        except Exception as e:
            print(f"Error grabbing frames: {e}")
            return None, None

    def get_depth_colormap(self, depth_image=None):
        """
        Convert depth image to colormap for visualization.

        Args:
            depth_image (numpy.ndarray): Depth image to convert. If None, grabs a new frame.

        Returns:
            numpy.ndarray: BGR colormap image, or None if failed
        """
        if depth_image is None:
            depth_image = self.get_depth_frame()

        if depth_image is None:
            return None

        # Apply colormap on depth image
        depth_colormap = cv2.applyColorMap(
            cv2.convertScaleAbs(depth_image, alpha=0.03),
            cv2.COLORMAP_JET
        )

        return depth_colormap

    def get_depth_scale(self):
        """
        Get the depth scale (units) of the camera.

        Returns:
            float: Depth scale (meters per unit), or None if not running
        """
        if not self.is_running or not self.profile:
            print("Camera is not running. Call start() first.")
            return None

        device = self.profile.get_device()
        depth_sensor = device.first_depth_sensor()
        return depth_sensor.get_depth_scale()

    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
        return False


if __name__ == "__main__":
    # Example usage
    print("Intel RealSense D435i Camera Test")
    print("-" * 40)

    # Create camera instance
    camera = IntelRealSenseD435i(width=640, height=480, fps=30)

    # Start camera
    if not camera.start():
        print("Failed to start camera")
        exit(1)

    try:
        print("\nPress 'q' to quit")
        print("Press 's' to save current frame")

        while True:
            # Get both frames
            bgr_frame = camera.get_bgr_frame()
            depth_frame = camera.get_depth_frame()

            if bgr_frame is None or depth_frame is None:
                print("Failed to get frames")
                continue

            # Get depth colormap for visualization
            depth_colormap = camera.get_depth_colormap(depth_frame)

            # Stack images horizontally for display
            images = np.hstack((bgr_frame, depth_colormap))

            # Display
            cv2.imshow("Intel RealSense D435i - BGR | Depth", images)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('s'):
                cv2.imwrite("realsense_bgr.jpg", bgr_frame)
                cv2.imwrite("realsense_depth.png", depth_frame)
                cv2.imwrite("realsense_depth_colormap.jpg", depth_colormap)
                print("Saved frames")

    finally:
        camera.stop()
        cv2.destroyAllWindows()

# Example usage:
# if __name__ == "__main__":
#     splitter.split()



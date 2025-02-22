import tkinter as tk

class ZeroPaddingLabel(tk.Frame):
    def __init__(self, master, text="Text", **kwargs):
        super().__init__(master, borderwidth=0, highlightthickness=0)
        
        # Method 1: Using Canvas
        self.canvas = tk.Canvas(
            self,
            borderwidth=0,
            highlightthickness=0,
            height=20,  # Set initial height
            width=100   # Set initial width
        )
        self.canvas.pack(fill="both", expand=True)
        
        # Create text on canvas
        self.text_id = self.canvas.create_text(
            0, 0,  # Place at top-left corner
            text=text,
            anchor="nw",  # Northwest anchor for top-left alignment
            **kwargs
        )
        
        # Update canvas size based on text
        self.update_canvas_size()
        
    def update_canvas_size(self):
        # Get text bounds
        bbox = self.canvas.bbox(self.text_id)
        if bbox:
            # Update canvas size to match text exactly
            self.canvas.configure(
                width=bbox[2] - bbox[0],
                height=bbox[3] - bbox[1]
            )
    
    def set_text(self, text):
        self.canvas.itemconfig(self.text_id, text=text)
        self.update_canvas_size()

# Alternative approach using Label
class MinimalLabel(tk.Label):
    def __init__(self, master, **kwargs):
        super().__init__(
            master,
            borderwidth=0,
            highlightthickness=0,
            padx=0,
            pady=0,
            **kwargs
        )

# Example usage
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Zero Padding Demo")
    
    # Frame for demonstration
    frame = tk.Frame(root, bg='red')
    frame.pack(padx=20, pady=20)
    
    # Using Canvas-based approach
    label1 = ZeroPaddingLabel(frame, text="No Padding (Canvas)", font=("Arial", 12))
    label1.pack()
    
    # Spacer
    tk.Frame(frame, height=10, bg='red').pack()
    
    # Using minimal Label approach
    label2 = MinimalLabel(
        frame,
        text="No Padding (Label)",
        font=("Arial", 12),
        bg='white'
    )
    label2.pack()
    
    root.mainloop()
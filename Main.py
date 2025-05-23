import math
import tkinter as tk
from tkinter import ttk, Frame, Scale, IntVar, StringVar, OptionMenu, scrolledtext
import heapq
from collections import deque
import random
import time
from AIAssistant import AIAssistant
from Simple_MARL_Integration import integrate_marl_with_app, do_shape_with_marl
from Simple_GA_Integration import integrate_ga_with_app, do_shape_with_ga

DEFAULT_GRID_SIZE = 10
MAX_CANVAS_SIZE = 600
GRID_COLOR = "#95A5A6"
ACTIVE_COLOR = "#FF9500"
INACTIVE_COLOR = "#F5F5F5"
OBSTACLE_COLOR = "#2C3E50"
OUTLINE_COLOR = "#2ECC71"
PATH_COLOR = "#3498DB"
MINIMAX_COLOR = "#9B59B6"
ALPHA_BETA_COLOR = "#E74C3C"
EXPECTIMAX_COLOR = "#1ABC9C"

HEADER_BG = "#34495E"
HEADER_FG = "white"
BUTTON_BG = "#3498DB"
BUTTON_FG = "white"
BUTTON_ACTIVE_BG = "#2980B9"
CANVAS_BG = "#ECF0F1"
FRAME_BG = "#F8F9FA"


class InteractiveGrid:
    def __init__(self, root):
        self.root = root
        self.root.title("Interactive Grid - Shape Formation Simulator")
        self.root.configure(bg=FRAME_BG)

        title_frame = tk.Frame(root, bg=HEADER_BG, padx=10, pady=10)
        title_frame.pack(fill=tk.X)

        title_container = tk.Frame(title_frame, bg=HEADER_BG)
        title_container.pack(fill=tk.X)

        title_label = tk.Label(title_container,
                              text="Interactive Grid - Shape Formation Simulator",
                              font=("Arial", 16, "bold"),
                              bg=HEADER_BG,
                              fg=HEADER_FG)
        title_label.pack(side=tk.LEFT)

        self.ai_assistant = AIAssistant(root)

        ai_button_style = {
            "bg": "#9B59B6",
            "fg": "white",
            "activebackground": "#8E44AD",
            "relief": tk.RAISED,
            "padx": 10,
            "pady": 5,
            "font": ("Arial", 10, "bold")
        }

        self.ai_button = tk.Button(title_container, text="AI Assistant",
                                  command=self.toggle_ai_assistant,
                                  **ai_button_style)
        self.ai_button.pack(side=tk.RIGHT, padx=10)

        self.speed_var = tk.IntVar(value=100)

        self.movement_speed = self.speed_var.get()

        self.speed_var.trace_add("write", self.update_movement_speed)

        self.grid_size = DEFAULT_GRID_SIZE
        self.grid_size_var = tk.IntVar(value=self.grid_size)

        self.agent_count = 20
        self.agent_count_var = tk.IntVar(value=self.agent_count)

        self.calculate_cell_size()


        main_frame = Frame(root, bg=FRAME_BG)
        main_frame.pack(padx=15, pady=15, fill=tk.BOTH, expand=True)

        left_frame = Frame(main_frame, bg=HEADER_BG, bd=2, relief=tk.RIDGE)
        left_frame.pack(side=tk.LEFT, padx=10, pady=10)

        self.canvas = tk.Canvas(left_frame, width=MAX_CANVAS_SIZE, height=MAX_CANVAS_SIZE,
                              bg=CANVAS_BG, bd=0, highlightthickness=0)
        self.canvas.pack(padx=5, pady=5)

        right_outer_frame = Frame(main_frame, bg=FRAME_BG, bd=2, relief=tk.RIDGE)
        right_outer_frame.pack(side=tk.LEFT, padx=10, pady=10, fill=tk.BOTH, expand=True)

        control_header = Frame(right_outer_frame, bg=HEADER_BG, padx=5, pady=5)
        control_header.pack(fill=tk.X)

        control_title = tk.Label(control_header, text="Control Panel",
                             font=("Arial", 12, "bold"), bg=HEADER_BG, fg=HEADER_FG)
        control_title.pack()

        control_canvas = tk.Canvas(right_outer_frame, bg=FRAME_BG, highlightthickness=0)
        control_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        control_scrollbar = tk.Scrollbar(right_outer_frame, orient=tk.VERTICAL, command=control_canvas.yview)
        control_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        control_canvas.configure(yscrollcommand=control_scrollbar.set)

        right_frame = Frame(control_canvas, bg=FRAME_BG, padx=10, pady=10)

        control_canvas_window = control_canvas.create_window((0, 0), window=right_frame, anchor=tk.NW)

        def configure_scroll_region(event):
            control_canvas.configure(scrollregion=control_canvas.bbox("all"))

        right_frame.bind("<Configure>", configure_scroll_region)

        def configure_canvas_width(event):
            canvas_width = event.width
            control_canvas.itemconfig(control_canvas_window, width=canvas_width)

        control_canvas.bind("<Configure>", configure_canvas_width)

        def _on_mousewheel(event):
            control_canvas.yview_scroll(int(-1*(event.delta/120)), "units")

        control_canvas.bind_all("<MouseWheel>", _on_mousewheel)

        self.cells = {}
        self.active_cells = []
        self.reserved_cells = set()
        self.visited_cells = set()

        self.custom_shape_mode = False
        self.custom_shape = []

        self.moving_cells = {}
        self.movement_timer = None

        self.movement_mode_var = tk.StringVar(value="sequential")

        self.MOVEMENT_MODES = {
            "sequential": "Sequential",
            "parallel": "Parallel",
            "f1_safety_car": "F1 Safety Car Queue (Decentralized)"
        }

        self.parallel_mode = False
        self.centralized_mode = False
        self.parallel_centralized_mode = False
        self.deadlock_counter = {}
        self.path_attempts = {}
        self.max_attempts = 3
        self.step_counter = 0

        self.metrics = {
            "A*": {
                "explored": 0, "path_length": 0, "time": 0, "moves": 0,
                "success_rate": 0,
                "completed_targets": 0,
                "total_targets": 0
            },
            "BFS": {
                "explored": 0, "path_length": 0, "time": 0, "moves": 0,
                "success_rate": 0,
                "completed_targets": 0,
                "total_targets": 0
            },
            "DFS": {
                "explored": 0, "path_length": 0, "time": 0, "moves": 0,
                "success_rate": 0,
                "completed_targets": 0,
                "total_targets": 0
            },
            "Minimax": {
                "explored": 0, "path_length": 0, "time": 0, "moves": 0,
                "success_rate": 0,
                "completed_targets": 0,
                "total_targets": 0
            },
            "Alpha-Beta": {
                "explored": 0, "path_length": 0, "time": 0, "moves": 0,
                "success_rate": 0,
                "completed_targets": 0,
                "total_targets": 0,
                "pruned": 0
            },
            "Expectimax": {
                "explored": 0, "path_length": 0, "time": 0, "moves": 0,
                "success_rate": 0,
                "completed_targets": 0,
                "total_targets": 0,
                "chance_nodes": 0
            }
        }
        self.current_algorithm = "A*"
        self.total_cells_to_fill = 0
        self.cells_filled = 0
        self.start_time = 0

        self.create_controls(right_frame)

        self.initialize_grid()

        self.canvas.bind("<Button-1>", self.toggle_obstacle)

        self.movement_started = False

        self.initialize_grid()
        self.layers = []
        self.current_layer = 0
        self.generate_layers()
        self.current_target = self.layers[self.current_layer] if self.layers else []

        self.marl_integration = integrate_marl_with_app(self)

        self.ga_planner = integrate_ga_with_app(self)



    def create_controls(self, parent):
        """Create UI controls."""
        grid_size_frame = Frame(parent)
        grid_size_frame.pack(pady=5, fill=tk.X)

        tk.Label(grid_size_frame, text="Grid Size:").pack(side=tk.LEFT)

        grid_size_entry = tk.Entry(grid_size_frame, textvariable=self.grid_size_var, width=5)
        grid_size_entry.pack(side=tk.LEFT, padx=5)

        apply_size_btn = tk.Button(grid_size_frame, text="Apply", command=self.apply_grid_size,
                                  bg=BUTTON_BG, fg=BUTTON_FG, activebackground=BUTTON_ACTIVE_BG,
                                  relief=tk.RAISED, padx=10)
        apply_size_btn.pack(side=tk.LEFT, padx=5)

        agent_count_frame = Frame(parent)
        agent_count_frame.pack(pady=5, fill=tk.X)

        tk.Label(agent_count_frame, text="Agent Count:").pack(side=tk.LEFT)

        agent_count_entry = tk.Entry(agent_count_frame, textvariable=self.agent_count_var, width=5)
        agent_count_entry.pack(side=tk.LEFT, padx=5)

        apply_agent_btn = tk.Button(agent_count_frame, text="Apply", command=self.apply_agent_count,
                                   bg=BUTTON_BG, fg=BUTTON_FG, activebackground=BUTTON_ACTIVE_BG,
                                   relief=tk.RAISED, padx=10)
        apply_agent_btn.pack(side=tk.LEFT, padx=5)

        speed_frame = Frame(parent)
        speed_frame.pack(pady=5, fill=tk.X)

        tk.Label(speed_frame, text="Movement Speed:").pack(side=tk.LEFT)

        speed_scale = Scale(speed_frame, from_=10, to=500, orient=tk.HORIZONTAL,
                           variable=self.speed_var, length=150)
        speed_scale.pack(side=tk.LEFT, padx=5)

        tk.Label(speed_frame, text="Fast").pack(side=tk.LEFT)
        tk.Label(speed_frame, text="Slow").pack(side=tk.RIGHT)

        shape_frame = Frame(parent)
        shape_frame.pack(pady=5, fill=tk.X)

        tk.Label(shape_frame, text="Shape:").pack(side=tk.LEFT)

        button_style = {
            "bg": BUTTON_BG,
            "fg": BUTTON_FG,
            "activebackground": BUTTON_ACTIVE_BG,
            "relief": tk.RAISED,
            "padx": 10
        }

        self.rectangle_btn = tk.Button(shape_frame, text="Rectangle", command=self.set_rectangle_shape, **button_style)
        self.rectangle_btn.pack(side=tk.LEFT, padx=2)

        self.triangle_btn = tk.Button(shape_frame, text="Triangle", command=self.set_triangle_shape, **button_style)
        self.triangle_btn.pack(side=tk.LEFT, padx=2)

        self.circle_btn = tk.Button(shape_frame, text="Circle", command=self.set_circle_shape, **button_style)
        self.circle_btn.pack(side=tk.LEFT, padx=2)

        self.custom_btn = tk.Button(shape_frame, text="Custom Shape", command=self.start_custom_shape, **button_style)
        self.custom_btn.pack(side=tk.LEFT, padx=2)

        self.finish_custom_btn = tk.Button(shape_frame, text="Finish Custom Shape",
                                         command=self.finish_custom_shape, **button_style)
        self.finish_custom_btn.pack(side=tk.LEFT, padx=2)
        self.finish_custom_btn.pack_forget()

        algo_frame = Frame(parent)
        algo_frame.pack(pady=5, fill=tk.X)

        tk.Label(algo_frame, text="Algorithm:").pack(side=tk.LEFT)

        self.algorithm_var = StringVar(value="A*")
        algorithms = ["A*", "BFS", "DFS", "Minimax", "Alpha-Beta", "Expectimax"]
        algo_menu = OptionMenu(algo_frame, self.algorithm_var, *algorithms)
        algo_menu.pack(side=tk.LEFT, padx=5)
        self.algorithm_var.trace_add("write", self.on_algorithm_change)

        movement_header = Frame(parent, bg=HEADER_BG, padx=5, pady=2)
        movement_header.pack(fill=tk.X, pady=(10, 0))

        tk.Label(movement_header, text="Movement Mode", font=("Arial", 10, "bold"),
                bg=HEADER_BG, fg=HEADER_FG).pack(anchor=tk.W)

        movement_options_frame = Frame(parent, bg=FRAME_BG)
        movement_options_frame.pack(pady=5, fill=tk.X)

        for mode_key, mode_name in self.MOVEMENT_MODES.items():
            rb = tk.Radiobutton(
                movement_options_frame,
                text=mode_name,
                variable=self.movement_mode_var,
                value=mode_key,
                command=self.update_movement_mode,
                bg=FRAME_BG
            )
            rb.pack(anchor=tk.W, padx=10, pady=2)

        action_header = Frame(parent, bg=HEADER_BG, padx=5, pady=2)
        action_header.pack(fill=tk.X, pady=(10, 0))

        tk.Label(action_header, text="Actions", font=("Arial", 10, "bold"),
                bg=HEADER_BG, fg=HEADER_FG).pack(anchor=tk.W)

        btn_frame = Frame(parent, bg=FRAME_BG)
        btn_frame.pack(pady=5, fill=tk.X)

        action_style = button_style.copy()
        action_style["font"] = ("Arial", 10, "bold")

        self.do_shape_btn = tk.Button(btn_frame, text="Do the Shape", command=self.start_movement,
                                     **action_style)
        self.do_shape_btn.pack(side=tk.LEFT, padx=5)

        self.reset_btn = tk.Button(btn_frame, text="Reset", command=self.reset_grid,
                                  **action_style)
        self.reset_btn.pack(side=tk.LEFT, padx=5)

        obstacles_header = Frame(parent, bg=HEADER_BG, padx=5, pady=2)
        obstacles_header.pack(fill=tk.X, pady=(10, 0))

        tk.Label(obstacles_header, text="Obstacles", font=("Arial", 10, "bold"),
                bg=HEADER_BG, fg=HEADER_FG).pack(anchor=tk.W)

        obstacles_frame = Frame(parent, bg=FRAME_BG)
        obstacles_frame.pack(pady=5, fill=tk.X)

        self.random_obstacles_button = tk.Button(obstacles_frame, text="Random Obstacles",
                                               command=self.add_random_obstacles, **button_style)
        self.random_obstacles_button.pack(side=tk.LEFT, padx=5)

        self.clear_obstacles_button = tk.Button(obstacles_frame, text="Clear Obstacles",
                                              command=self.clear_obstacles, **button_style)
        self.clear_obstacles_button.pack(side=tk.LEFT, padx=5)

        status_header = Frame(parent, bg=HEADER_BG, padx=5, pady=2)
        status_header.pack(fill=tk.X, pady=(10, 0))

        tk.Label(status_header, text="Status", font=("Arial", 10, "bold"),
                bg=HEADER_BG, fg=HEADER_FG).pack(anchor=tk.W)

        status_frame = Frame(parent, bg=FRAME_BG, bd=1, relief=tk.SUNKEN)
        status_frame.pack(pady=5, fill=tk.BOTH, expand=True)

        self.status_text = scrolledtext.ScrolledText(status_frame, width=30, height=10, wrap=tk.WORD,
                                                   bg=CANVAS_BG, font=("Consolas", 9))
        self.status_text.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        self.status_text.config(state=tk.DISABLED)

        metrics_header = Frame(parent, bg=HEADER_BG, padx=5, pady=2)
        metrics_header.pack(fill=tk.X, pady=(10, 0))

        tk.Label(metrics_header, text="Performance Metrics", font=("Arial", 10, "bold"),
                bg=HEADER_BG, fg=HEADER_FG).pack(anchor=tk.W)

        metrics_frame = Frame(parent, bg=FRAME_BG, bd=1, relief=tk.SUNKEN)
        metrics_frame.pack(pady=5, fill=tk.BOTH, expand=True)

        self.metrics_text = scrolledtext.ScrolledText(metrics_frame, width=30, height=15, wrap=tk.WORD,
                                                    bg=CANVAS_BG, font=("Consolas", 9))
        self.metrics_text.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        self.metrics_text.config(state=tk.DISABLED)



        compare_frame = Frame(parent, bg=FRAME_BG)
        compare_frame.pack(pady=10, fill=tk.X)

        compare_style = {
            "bg": "#E74C3C",
            "fg": "white",
            "activebackground": "#C0392B",
            "relief": tk.RAISED,
            "padx": 10,
            "pady": 5,
            "font": ("Arial", 10, "bold")
        }

        self.compare_btn = tk.Button(compare_frame, text="Compare All Algorithms",
                                   command=self.compare_algorithms, **compare_style)
        self.compare_btn.pack(side=tk.LEFT, padx=5)





    def toggle_ai_assistant(self):
        """Toggle the AI Assistant window visibility."""
        try:
            # Check if window exists and is visible
            state = self.ai_assistant.window.state()
            if state == 'normal':
                self.ai_assistant.hide()
            else:
                self.ai_assistant.show()
        except:
            # If there's an error, recreate the assistant
            self.ai_assistant = AIAssistant(self.root)
            self.ai_assistant.show()

    def update_movement_speed(self, *args):
        """Update the movement speed when the slider changes."""
        self.movement_speed = self.speed_var.get()
        self.update_status(f"Movement speed set to {self.movement_speed} ms")



    def calculate_cell_size(self):
        """Calculate the cell size based on the grid dimensions."""
        # Calculate cell size to fit the grid within MAX_CANVAS_SIZE
        self.cell_size = min(MAX_CANVAS_SIZE // self.grid_size, 40)  # Max cell size is 40 pixels

    def update_movement_mode(self):
        """Update the movement mode based on the selected radio button."""
        selected_mode = self.movement_mode_var.get()

        # Update the legacy variables for backward compatibility
        self.parallel_mode = (selected_mode == "parallel")
        self.centralized_mode = False  # No longer using sequential_centralized
        self.parallel_centralized_mode = (selected_mode == "f1_safety_car")

        # Get the display name of the selected mode
        mode_display_name = self.MOVEMENT_MODES.get(selected_mode, "Unknown")

        self.update_status(f"Movement mode changed to {mode_display_name}")

    def apply_grid_size(self):
        """Apply the new grid size and reinitialize the grid."""
        if self.movement_started:
            self.update_status("Cannot change grid size while movement is in progress.")
            return

        try:
            # Get the new grid size from the entry field
            new_size = int(self.grid_size_var.get())

            # Ensure grid size is at least 1
            if new_size < 1:
                self.update_status("Grid size must be at least 1.")
                return

            if new_size != self.grid_size:
                self.grid_size = new_size

                # Recalculate cell size based on new grid dimensions
                self.calculate_cell_size()

                # Canvas size remains fixed at MAX_CANVAS_SIZE

                # Reinitialize the grid with the new size
                self.initialize_grid()

                self.update_status(f"Grid size changed to {self.grid_size}x{self.grid_size}.")
        except ValueError:
            self.update_status("Please enter a valid number for grid size.")

    def apply_agent_count(self):
        """Apply the new agent count and reinitialize the grid."""
        if self.movement_started:
            self.update_status("Cannot change agent count while movement is in progress.")
            return

        try:
            # Get the new agent count from the entry field
            new_count = int(self.agent_count_var.get())

            # Ensure agent count is at least 1
            if new_count < 1:
                self.update_status("Agent count must be at least 1.")
                return

            if new_count != self.agent_count:
                self.agent_count = new_count

                # Reinitialize the grid with the new agent count
                self.initialize_grid()

                self.update_status(f"Agent count changed to {self.agent_count}.")
        except ValueError:
            self.update_status("Please enter a valid number for agent count.")

    def generate_layers(self):
        """Generate layers (outlines) for the target shape."""
        remaining_shape = self.target_shape.copy()
        self.layers = []
        while remaining_shape:
            inner, outline, _ = self.separate_cells(remaining_shape)
            if not outline:
                self.layers.append(remaining_shape)
                break
            self.layers.append(outline)
            remaining_shape = inner


    def on_algorithm_change(self, *args):
        """Handle algorithm change and update AI assistant with algorithm info."""
        algorithm = self.algorithm_var.get()
        self.current_algorithm = algorithm
        self.update_status(f"Algorithm changed to {algorithm}")

        # If AI assistant is visible, show algorithm explanation
        try:
            if hasattr(self, 'ai_assistant') and self.ai_assistant.window.state() == 'normal':
                explanation = self.ai_assistant.algorithm_explanations.get(algorithm,
                    f"No specific information available for {algorithm}.")
                self.ai_assistant.display_message(
                    f"Algorithm changed to {algorithm}. {explanation}", "assistant")
        except:
            pass  # Ignore errors if AI assistant is not available

    def update_status(self, message):
        """Update status text."""
        self.status_text.config(state=tk.NORMAL)
        self.status_text.insert(tk.END, message + "\n")
        self.status_text.see(tk.END)
        self.status_text.config(state=tk.DISABLED)

    def update_metrics_display(self):
        """Update the metrics display with current data."""
        self.metrics_text.config(state=tk.NORMAL)
        self.metrics_text.delete(1.0, tk.END)

        # For the current algorithm, show detailed metrics
        algo = self.current_algorithm
        self.metrics_text.insert(tk.END, f"Current Algorithm: {algo}\n")
        self.metrics_text.insert(tk.END, f"------------------------\n")

        # Check if the algorithm exists in metrics
        if algo not in self.metrics:
            # Add the algorithm to metrics with the new structure
            self.metrics[algo] = {
                "explored": 0, "path_length": 0, "time": 0, "moves": 0,
                "success_rate": 0, "completed_targets": 0, "total_targets": 0
            }
            self.metrics_text.insert(tk.END, "No data yet for this algorithm.\n")
        elif self.metrics[algo]["moves"] > 0:
            total_time = self.metrics[algo]["time"]
            avg_explored = self.metrics[algo]["explored"] / self.metrics[algo]["moves"]
            avg_path = self.metrics[algo]["path_length"] / self.metrics[algo]["moves"]

            # Get the success rate directly
            success_rate = self.metrics[algo]["success_rate"]
            completed_targets = self.metrics[algo]["completed_targets"]
            total_targets = self.metrics[algo]["total_targets"]

            self.metrics_text.insert(tk.END,
                                     f"Cells explored: {self.metrics[algo]['explored']} (Avg: {avg_explored:.2f})\n")
            self.metrics_text.insert(tk.END,
                                     f"Path length: {self.metrics[algo]['path_length']} (Avg: {avg_path:.2f})\n")
            self.metrics_text.insert(tk.END, f"Time: {total_time:.4f}s\n")
            self.metrics_text.insert(tk.END, f"Success rate: {success_rate:.1f}%\n")
            self.metrics_text.insert(tk.END, f"Completed targets: {completed_targets}/{total_targets}\n")

            # Show pruned nodes for Alpha-Beta
            if algo == "Alpha-Beta" and "pruned" in self.metrics[algo]:
                pruned = self.metrics[algo]["pruned"]
                if pruned > 0:
                    self.metrics_text.insert(tk.END, f"Nodes pruned: {pruned}\n")
                    pruning_efficiency = (pruned / self.metrics[algo]['explored']) * 100
                    self.metrics_text.insert(tk.END, f"Pruning efficiency: {pruning_efficiency:.2f}%\n")

            # Show chance nodes for Expectimax
            if algo == "Expectimax" and "chance_nodes" in self.metrics[algo]:
                chance_nodes = self.metrics[algo]["chance_nodes"]
                if chance_nodes > 0:
                    self.metrics_text.insert(tk.END, f"Chance nodes: {chance_nodes}\n")
                    chance_ratio = (chance_nodes / self.metrics[algo]['explored']) * 100
                    self.metrics_text.insert(tk.END, f"Chance node ratio: {chance_ratio:.2f}%\n")

            if self.movement_started:
                # Show progress for current shape
                progress = (self.cells_filled / self.total_cells_to_fill) * 100 if self.total_cells_to_fill > 0 else 0
                elapsed = time.time() - self.start_time
                self.metrics_text.insert(tk.END, f"\nCurrent progress: {progress:.1f}%\n")
                self.metrics_text.insert(tk.END, f"Time elapsed: {elapsed:.2f}s\n")
        else:
            self.metrics_text.insert(tk.END, "No data yet for this algorithm.\n")

        self.metrics_text.insert(tk.END, f"\nSummary of All Algorithms:\n")
        self.metrics_text.insert(tk.END, f"------------------------\n")

        # Show summary for all algorithms
        for alg in ["A*", "BFS", "DFS", "Minimax", "Alpha-Beta", "Expectimax"]:
            if alg in self.metrics and self.metrics[alg]["moves"] > 0:
                total_time = self.metrics[alg]["time"]
                success_rate = self.metrics[alg]["success_rate"]

                self.metrics_text.insert(tk.END,
                    f"{alg}: Time: {total_time:.4f}s, Success rate: {success_rate:.1f}%\n")
            else:
                self.metrics_text.insert(tk.END, f"{alg}: No data yet\n")

        self.metrics_text.config(state=tk.DISABLED)

    def initialize_grid(self):
        """Initialize the grid with default settings."""
        # Clear the canvas
        self.canvas.delete("all")

        # Reset data structures
        self.cells = {}
        self.active_cells = []
        self.reserved_cells = set()
        self.visited_cells = set()
        self.cells_filled = 0

        # Draw the grid
        for row in range(self.grid_size):
            for col in range(self.grid_size):
                x1, y1 = col * self.cell_size, row * self.cell_size
                x2, y2 = x1 + self.cell_size, y1 + self.cell_size

                # Initially all cells are inactive
                is_active = False
                fill_color = INACTIVE_COLOR
                rect = self.canvas.create_rectangle(x1, y1, x2, y2, fill=fill_color, outline=GRID_COLOR)

                self.cells[(row, col)] = {
                    "rect": rect,
                    "active": is_active,
                    "obstacle": False
                }

        # Create active agents based on agent_count
        self.active_cells = []

        # Determine how many rows we need
        cells_per_row = min(self.grid_size, 10)  # Maximum 10 cells per row
        num_rows_needed = (self.agent_count + cells_per_row - 1) // cells_per_row  # Ceiling division

        # Start from the bottom row and work upwards
        remaining_cells = self.agent_count

        for row_offset in range(num_rows_needed):
            current_row = self.grid_size - 1 - row_offset

            # Calculate how many cells to place in this row
            cells_in_this_row = min(remaining_cells, cells_per_row)

            # Center the cells in the row
            start_col = (self.grid_size - cells_in_this_row) // 2

            # Place cells in this row
            for col in range(start_col, start_col + cells_in_this_row):
                cell = (current_row, col)
                self.cells[cell]["active"] = True
                self.canvas.itemconfig(self.cells[cell]["rect"], fill=ACTIVE_COLOR)
                self.active_cells.append(cell)
                remaining_cells -= 1

            # If we've placed all cells, break
            if remaining_cells <= 0:
                break

        # Set default shape (rectangle)
        self.target_shape = self.define_target_rectangle()
        self.inner_cells, self.outline_cells, self.corner_cells = self.separate_cells()
        self.draw_green_outline()

        # Update total cells to fill
        self.total_cells_to_fill = len(self.target_shape)

        # Update status
        self.update_status("Grid initialized with rectangle shape.")
        self.movement_started = False

        # Update metrics display
        self.update_metrics_display()

    def define_target_rectangle(self):
        """Creates a 5x4 rectangle in the grid center (rows 3–6, columns 3–7)."""
        mid_row, mid_col = self.grid_size // 2, self.grid_size // 2
        return [(mid_row - 2 + r, mid_col - 2 + c) for r in range(4) for c in range(5)]

    def define_target_triangle(self):
        """
        Creates a large triangle placed two rows above the bottom two orange cells.
        The triangle has:
        - Base row: row 6 with 8 cells (columns 1 to 8)
        - Next row: row 5 with 6 cells (columns 2 to 7)
        - Next row: row 4 with 4 cells (columns 3 to 6)
        - Top row: row 3 with 2 cells (columns 4 to 5)
        """
        shape = []
        # Base row: row 6, columns 1..8
        for c in range(1, 9):
            shape.append((6, c))
        # Next row: row 5, columns 2..7
        for c in range(2, 8):
            shape.append((5, c))
        # Next row: row 4, columns 3..6
        for c in range(3, 7):
            shape.append((4, c))
        # Top row: row 3, columns 4..5
        for c in range(4, 6):
            shape.append((3, c))
        return shape

    def define_target_circle(self):
        """
        Creates a circle (oval) shape with a custom pattern spanning 6 rows.
        The pattern (relative to the shape's own rows) is:
        - Row 1: 2 cells at columns 4 and 5
        - Row 2: 4 cells at columns 3,4,5,6
        - Row 3: 2 cells (columns 2,3), then a gap (columns 4,5), then 2 cells (columns 6,7)
        - Row 4: same as Row 3
        - Row 5: 4 cells at columns 3,4,5,6
        - Row 6: 2 cells at columns 4 and 5
        These rows are mapped to grid rows 1 to 6.
        """
        shape = []
        # Row 1 (grid row 1): 2 cells at columns 4 and 5
        for c in [4, 5]:
            shape.append((1, c))
        # Row 2 (grid row 2): 4 cells at columns 3,4,5,6
        for c in range(3, 7):
            shape.append((2, c))
        # Row 3 (grid row 3): cells at columns 2,3 and 6,7
        for c in [2, 3, 6, 7]:
            shape.append((3, c))
        # Row 4 (grid row 4): same as row 3
        for c in [2, 3, 6, 7]:
            shape.append((4, c))
        # Row 5 (grid row 5): 4 cells at columns 3,4,5,6
        for c in range(3, 7):
            shape.append((5, c))
        # Row 6 (grid row 6): 2 cells at columns 4 and 5
        for c in [4, 5]:
            shape.append((6, c))
        return shape

    def set_rectangle_shape(self):
        """Switch to the rectangle shape."""
        # Force reshaping if there are active cells (shape is completed or in progress)
        active_cells_exist = False
        for cell in self.cells:
            if self.cells[cell]["active"]:
                active_cells_exist = True
                break

        if self.movement_started or active_cells_exist:
            # If movement has started or shape is completed, call reshape
            self.reshape("rectangle")
            return

        self.remove_green_outline()
        self.target_shape = self.define_target_rectangle()
        self.inner_cells, self.outline_cells, self.corner_cells = self.separate_cells()
        self.draw_green_outline()
        self.total_cells_to_fill = len(self.target_shape)
        self.update_status("Shape changed to rectangle.")

        # Update AI assistant if visible
        try:
            if hasattr(self, 'ai_assistant') and self.ai_assistant.window.state() == 'normal':
                self.ai_assistant.display_message(
                    "Rectangle shape selected. This is a simple 5x4 rectangle placed in the center of the grid. "
                    "Agents will move to form this shape using the selected pathfinding algorithm.",
                    "assistant")
        except:
            pass

    def set_triangle_shape(self):
        """Switch to the triangle shape."""
        # Force reshaping if there are active cells (shape is completed or in progress)
        active_cells_exist = False
        for cell in self.cells:
            if self.cells[cell]["active"]:
                active_cells_exist = True
                break

        if self.movement_started or active_cells_exist:
            # If movement has started or shape is completed, call reshape
            self.reshape("triangle")
            return

        self.remove_green_outline()
        self.target_shape = self.define_target_triangle()
        self.inner_cells, self.outline_cells, self.corner_cells = self.separate_cells()
        self.draw_green_outline()
        self.total_cells_to_fill = len(self.target_shape)
        self.update_status("Shape changed to triangle.")

        # Update AI assistant if visible
        try:
            if hasattr(self, 'ai_assistant') and self.ai_assistant.window.state() == 'normal':
                self.ai_assistant.display_message(
                    "Triangle shape selected. This is a triangular shape with a wide base and narrowing toward the top. "
                    "The triangle has 20 cells arranged in 4 rows. Agents will move to form this shape using the selected algorithm.",
                    "assistant")
        except:
            pass

    def set_circle_shape(self):
        """Switch to the circle shape."""
        # Force reshaping if there are active cells (shape is completed or in progress)
        active_cells_exist = False
        for cell in self.cells:
            if self.cells[cell]["active"]:
                active_cells_exist = True
                break

        if self.movement_started or active_cells_exist:
            # If movement has started or shape is completed, call reshape
            self.reshape("circle")
            return

        self.remove_green_outline()
        self.target_shape = self.define_target_circle()
        self.inner_cells, self.outline_cells, self.corner_cells = self.separate_cells()
        self.draw_green_outline()
        self.total_cells_to_fill = len(self.target_shape)
        self.update_status("Shape changed to circle.")

        # Update AI assistant if visible
        try:
            if hasattr(self, 'ai_assistant') and self.ai_assistant.window.state() == 'normal':
                self.ai_assistant.display_message(
                    "Circle shape selected. This is an oval shape created with a custom pattern of 18 cells. "
                    "The shape has a hollow center and spans 6 rows. Agents will move to form this shape using the selected algorithm.",
                    "assistant")
        except:
            pass

    def start_custom_shape(self):
        """Start custom shape drawing mode."""
        # If movement is in progress, we need to pause it
        if self.movement_started:
            self.update_status("Cannot start custom shape mode while movement is in progress. Please finish or reset first.")
            return

        # Clear any existing shape
        self.remove_green_outline()
        self.custom_shape = []
        self.target_shape = []

        # Enter custom shape mode
        self.custom_shape_mode = True

        # Show the finish button
        self.finish_custom_btn.pack(side=tk.LEFT, padx=2)

        # Disable other shape buttons
        self.rectangle_btn.config(state=tk.DISABLED)
        self.triangle_btn.config(state=tk.DISABLED)
        self.circle_btn.config(state=tk.DISABLED)
        self.custom_btn.config(state=tk.DISABLED)

        # Update status
        self.update_status("Custom shape mode: Click on cells to create your shape. Click 'Finish Custom Shape' when done.")

        # Update AI assistant if visible
        try:
            if hasattr(self, 'ai_assistant') and self.ai_assistant.window.state() == 'normal':
                self.ai_assistant.display_message(
                    "Custom shape mode activated. Click on grid cells to add them to your shape. "
                    "When you're done, click 'Finish Custom Shape' to set it as the target. "
                    "Try to create a connected shape for best results.",
                    "assistant")
        except:
            pass

    def finish_custom_shape(self):
        """Finish custom shape drawing and apply it."""
        if not self.custom_shape_mode:
            return

        # Exit custom shape mode
        self.custom_shape_mode = False

        # Hide the finish button
        self.finish_custom_btn.pack_forget()

        # Enable shape buttons
        self.rectangle_btn.config(state=tk.NORMAL)
        self.triangle_btn.config(state=tk.NORMAL)
        self.circle_btn.config(state=tk.NORMAL)
        self.custom_btn.config(state=tk.NORMAL)

        # If no cells were selected, revert to rectangle
        if not self.custom_shape:
            self.set_rectangle_shape()
            self.update_status("No cells selected for custom shape. Reverted to rectangle.")
            return

        # Check if movement is already in progress
        if self.movement_started:
            # Call reshape with the custom shape
            self.reshape("custom")
            return

        # Apply the custom shape
        self.target_shape = self.custom_shape.copy()
        self.inner_cells, self.outline_cells, self.corner_cells = self.separate_cells()

        # Reset all custom shape cells to inactive color first
        for cell in self.custom_shape:
            if cell in self.cells and not self.cells[cell]["active"] and not self.cells[cell]["obstacle"]:
                self.canvas.itemconfig(self.cells[cell]["rect"], fill=INACTIVE_COLOR)

        # Then draw the green outline (this adds the outline_rect property to cells)
        self.draw_green_outline()
        self.total_cells_to_fill = len(self.target_shape)
        self.update_status(f"Custom shape created with {len(self.target_shape)} cells.")

        # Update AI assistant if visible
        try:
            if hasattr(self, 'ai_assistant') and self.ai_assistant.window.state() == 'normal':
                self.ai_assistant.display_message(
                    f"Custom shape created with {len(self.target_shape)} cells. "
                    f"Click 'Do the Shape' to start the simulation with the {self.current_algorithm} algorithm. "
                    f"You can also add obstacles before starting.",
                    "assistant")
        except:
            pass

    def separate_cells(self, target_cells=None):
        if target_cells is None:
            target_cells = self.target_shape  # Fallback for legacy calls
        if not target_cells:
            return [], [], []

        min_row = min(c[0] for c in target_cells)
        max_row = max(c[0] for c in target_cells)
        min_col = min(c[1] for c in target_cells)
        max_col = max(c[1] for c in target_cells)

        corners = [
            (min_row, min_col), (min_row, max_col),
            (max_row, max_col), (max_row, min_col)
        ]

        outline = []
        inner = []
        for cell in target_cells:
            if cell in corners:
                continue
            if (cell[0] in (min_row, max_row)) or (cell[1] in (min_col, max_col)):
                outline.append(cell)
            else:
                inner.append(cell)

        return inner, outline, corners

    def draw_green_outline(self):
        """Draws the green outline for the current target shape."""
        for cell in self.target_shape:
            row, col = cell
            if 0 <= row < self.grid_size and 0 <= col < self.grid_size:
                x1, y1 = col * self.cell_size, row * self.cell_size
                x2, y2 = x1 + self.cell_size, y1 + self.cell_size
                rect = self.canvas.create_rectangle(x1, y1, x2, y2, fill=OUTLINE_COLOR, outline=GRID_COLOR)
                self.cells[cell]["outline_rect"] = rect

    def remove_green_outline(self):
        """Removes the green outline for the current target shape."""
        for cell in self.target_shape:
            if cell in self.cells:
                # Remove the outline rectangle if it exists
                if "outline_rect" in self.cells[cell]:
                    self.canvas.delete(self.cells[cell]["outline_rect"])
                    del self.cells[cell]["outline_rect"]

                # Also ensure the cell color is reset if it's not active or an obstacle
                # This is especially important for custom shapes
                if not self.cells[cell]["active"] and not self.cells[cell]["obstacle"]:
                    self.canvas.itemconfig(self.cells[cell]["rect"], fill=INACTIVE_COLOR)

    def toggle_obstacle(self, event):
        """
        Toggles a cell's obstacle status on click (disabled once movement starts).
        In custom shape mode, adds/removes cells to/from the custom shape.
        """
        if self.movement_started:
            return

        col = event.x // self.cell_size
        row = event.y // self.cell_size

        if not (0 <= row < self.grid_size and 0 <= col < self.grid_size):
            return

        cell = (row, col)

        # Handle custom shape mode
        if self.custom_shape_mode:
            # Toggle cell in custom shape
            if cell in self.custom_shape:
                # Remove from custom shape
                self.custom_shape.remove(cell)
                # Reset cell color
                fill_color = ACTIVE_COLOR if self.cells[cell]["active"] else INACTIVE_COLOR
                if self.cells[cell]["obstacle"]:
                    fill_color = OBSTACLE_COLOR
                self.canvas.itemconfig(self.cells[cell]["rect"], fill=fill_color)
                self.update_status(f"Removed cell {cell} from custom shape. Total cells: {len(self.custom_shape)}")
            else:
                # Add to custom shape if not an active cell
                if not self.cells[cell]["active"]:
                    self.custom_shape.append(cell)
                    # Set cell color to outline color
                    self.canvas.itemconfig(self.cells[cell]["rect"], fill=OUTLINE_COLOR)
                    self.update_status(f"Added cell {cell} to custom shape. Total cells: {len(self.custom_shape)}")
            return

        # Normal obstacle toggling mode
        # Don't allow toggling active cells or target shape cells
        if cell in self.cells and not self.cells[cell]["active"] and cell not in self.target_shape:
            if self.cells[cell]["obstacle"]:
                self.canvas.itemconfig(self.cells[cell]["rect"], fill=INACTIVE_COLOR)
                self.cells[cell]["obstacle"] = False
                self.update_status(f"Removed obstacle at ({row}, {col})")
            else:
                self.canvas.itemconfig(self.cells[cell]["rect"], fill=OBSTACLE_COLOR)
                self.cells[cell]["obstacle"] = True
                self.update_status(f"Added obstacle at ({row}, {col})")

    def add_random_obstacles(self):
        """Add random obstacles to the grid."""
        if self.movement_started:
            return

        # Clear existing obstacles
        self.clear_obstacles()

        # Number of obstacles to add (adjust as needed)
        num_obstacles = random.randint(10, min(30, self.grid_size * 2))

        for _ in range(num_obstacles):
            row = random.randint(0, self.grid_size - 1)
            col = random.randint(0, self.grid_size - 1)
            cell = (row, col)

            # Don't add obstacles in active cells or target shape
            if cell in self.active_cells or cell in self.target_shape:
                continue

            self.cells[cell]["obstacle"] = True
            self.canvas.itemconfig(self.cells[cell]["rect"], fill=OBSTACLE_COLOR)

        self.update_status("Added random obstacles.")

    def clear_obstacles(self):
        """Clear all obstacles from the grid."""
        if self.movement_started:
            return

        for cell in self.cells:
            if self.cells[cell]["obstacle"]:
                self.cells[cell]["obstacle"] = False
                fill_color = ACTIVE_COLOR if cell in self.active_cells else INACTIVE_COLOR
                self.canvas.itemconfig(self.cells[cell]["rect"], fill=fill_color)

        self.update_status("Cleared all obstacles.")

    def reset_grid(self):
        """
        Perform a hard reset of the grid, immediately stopping any movement with no auto-restart.
        """
        # 1. Stop all ongoing movements
        self.movement_started = False

        # 2. Cancel ALL pending timers
        if hasattr(self, "movement_timer") and self.movement_timer:
            self.root.after_cancel(self.movement_timer)
            self.movement_timer = None

        # Cancel any other potential callbacks that might be in the queue
        for after_id in self.root.tk.call('after', 'info'):
            try:
                self.root.after_cancel(after_id)
            except Exception:
                pass

        # 3. Reset all movement-related data structures
        self.moving_cells = {}
        self.deadlock_counter = {}
        self.path_attempts = {}
        self.step_counter = 0
        self.reserved_cells = set()
        self.visited_cells = set()

        # 4. Enable the "Do the Shape" button
        if hasattr(self, "do_shape_btn"):
            self.do_shape_btn.config(state=tk.NORMAL)

        # 5. Clear the canvas
        self.canvas.delete("all")

        # 6. Reinitialize the grid
        self.initialize_grid()

        # 7. Rebind click events (in case they were unbound during movement)
        self.canvas.bind("<Button-1>", self.toggle_obstacle)

        # 8. Update status
        self.update_status("Grid has been reset.")

    def assign_targets(self):
        """Assign target cells to active cells using the Hungarian algorithm."""
        if not self.active_cells or not self.target_shape:
            return

        # Create cost matrix
        cost_matrix = []
        for active_cell in self.active_cells:
            row = []
            for target_cell in self.target_shape:
                # Manhattan distance as cost
                cost = abs(active_cell[0] - target_cell[0]) + abs(active_cell[1] - target_cell[1])
                row.append(cost)
            cost_matrix.append(row)

        # Find optimal assignment using a greedy approach
        self.cell_targets = {}
        active_cells = self.active_cells.copy()
        target_cells = self.target_shape.copy()

        while active_cells and target_cells:
            # Find the minimum cost assignment
            min_cost = float('inf')
            min_active_idx = -1
            min_target_idx = -1

            for i, active_cell in enumerate(active_cells):
                for j, target_cell in enumerate(target_cells):
                    cost = abs(active_cell[0] - target_cell[0]) + abs(active_cell[1] - target_cell[1])
                    if cost < min_cost:
                        min_cost = cost
                        min_active_idx = i
                        min_target_idx = j

            # Assign the minimum cost pair
            self.cell_targets[active_cells[min_active_idx]] = target_cells[min_target_idx]

            # Remove the assigned cells
            active_cells.pop(min_active_idx)
            target_cells.pop(min_target_idx)

        self.update_status("Targets assigned to active cells.")

    # def get_control_mode_name(self):
    #     """Get the name of the current control mode."""
    #     return "centralized" if self.centralized_mode else "distributed"

    def start_movement(self):
        """Start the movement of active cells to form the target shape."""
        if self.movement_started or not self.active_cells:
            self.update_status("Cannot start movement: either movement already started or no active cells")
            return

        self.movement_started = True
        self.do_shape_btn.config(state=tk.DISABLED)

        # Clear target shape overlay
        self.remove_green_outline()

        # For custom shapes, ensure all cells are properly reset to inactive color
        for cell in self.target_shape:
            if cell in self.cells and not self.cells[cell]["active"] and not self.cells[cell]["obstacle"]:
                self.canvas.itemconfig(self.cells[cell]["rect"], fill=INACTIVE_COLOR)

        # Assign targets to active cells
        self.assign_targets()

        # Start timing
        self.start_time = time.time()
        self.cells_filled = 0

        # Debug output for movement modes
        self.update_status(f"Parallel mode: {self.parallel_mode}")
        self.update_status(f"Centralized mode: {self.centralized_mode}")
        self.update_status(f"Parallel Centralized mode: {self.parallel_centralized_mode}")

        # Update AI assistant if visible
        try:
            if hasattr(self, 'ai_assistant') and self.ai_assistant.window.state() == 'normal':
                movement_type = "decentralized F1 safety car queue" if self.parallel_centralized_mode else "parallel (all agents move simultaneously)" if self.parallel_mode else "sequential (one agent at a time)"
                self.ai_assistant.display_message(
                    f"Starting simulation with {self.current_algorithm} algorithm in {movement_type} mode. "
                    f"The agents will now find paths to their assigned targets using {self.current_algorithm}. "
                    f"Watch as they navigate around obstacles and other agents to form the shape.",
                    "assistant")
        except:
            pass

        # Get the current movement mode
        movement_mode = self.movement_mode_var.get()

        # Update legacy variables for backward compatibility
        self.parallel_mode = (movement_mode == "parallel")
        self.centralized_mode = False  # No longer using sequential_centralized
        self.parallel_centralized_mode = (movement_mode == "f1_safety_car")

        # Check if we should use MARL for parallel movement
        if hasattr(self, 'marl_integration') and self.marl_integration:
            # Check if marl_integration is a dictionary (Simple_MARL_Integration)
            if isinstance(self.marl_integration, dict) and self.marl_integration.get('marl') is not None:
                # Use MARL for parallel movement (Simple_MARL_Integration)
                self.update_status("Using MARL for parallel decentralized movement")
                do_shape_with_marl(self)
                return
            # Check if marl_integration is an object with marl attribute (MARL_Integration_For_Parallel)
            elif hasattr(self.marl_integration, 'marl') and self.marl_integration.marl is not None:
                # Use MARL for parallel movement (MARL_Integration_For_Parallel)
                self.update_status("Using MARL for parallel movement")
                self.marl_integration.do_shape_with_marl(self)
                return

        # Check if we should use GA for movement
        if hasattr(self, 'ga_planner') and self.ga_planner:
            # Check if ga_planner is a dictionary (Simple_GA_Integration)
            if isinstance(self.ga_planner, dict) and self.ga_planner.get('ga') is not None:
                # Use GA for movement (Simple_GA_Integration)
                self.update_status("Using Genetic Algorithm for movement")
                do_shape_with_ga(self)
                return
            # Check if ga_planner is an object (GeneticAlgorithmIntegration)
            elif hasattr(self.ga_planner, 'ga') and self.ga_planner.ga is not None:
                # Use GA for movement (GeneticAlgorithmIntegration)
                self.update_status("Using Genetic Algorithm for movement")
                self.ga_planner.do_shape_with_ga()
                return

        # Start the appropriate movement process based on the selected mode
        if movement_mode == "f1_safety_car":
            # Start decentralized F1 safety car queue movement
            self.update_status("Starting decentralized F1 safety car queue movement")
            self.start_parallel_centralized_movement()
        elif movement_mode == "parallel":
            # Start parallel movement
            self.update_status("Starting parallel movement")
            self.movement_timer = self.root.after(50, self.process_parallel_movements)
        else:
            # Default to sequential movement
            self.update_status(f"Starting sequential movement with {self.current_algorithm} algorithm.")
            self.move_next_square()

    def process_parallel_movements(self):
        """
        Main movement process for parallel mode with improved cell targeting.
        Ensures all cells in shapes, especially circles, are properly filled.
        """
        # Increment global step counter
        self.step_counter += 1

        # Update all currently moving cells
        self.update_moving_cells()

        # Run deadlock detection and resolution every 5 steps
        if self.step_counter % 5 == 0:
            self.detect_and_resolve_deadlocks()

        # Check if current layer is filled
        current_layer_filled = all(self.cells[cell]["active"] for cell in self.current_target)
        if current_layer_filled and self.current_layer < len(self.layers) - 1:
            # Move to next layer
            self.current_layer += 1
            self.current_target = self.layers[self.current_layer]
            # Reactivate previous layer's cells
            for cell in self.layers[self.current_layer - 1]:
                if self.cells[cell]["active"]:
                    self.active_cells.append(cell)
            # Reset path attempts
            self.path_attempts.clear()

        # Clear path attempts every 30 steps to allow retrying
        if self.step_counter % 30 == 0:
            self.path_attempts.clear()

            # Specifically check for unfilled cells and mark them for targeting
            unfilled_targets = [cell for cell in self.target_shape if not self.cells[cell]["active"]]
            if unfilled_targets:
                self.update_status(f"Prioritizing {len(unfilled_targets)} unfilled cells...")
                # Reset attempt counters to force retrying
                for target in unfilled_targets:
                    if target in self.path_attempts:
                        self.path_attempts[target] = 0

        # Check if we're done
        if not self.active_cells and not self.moving_cells:
            self.finish_movement(success=False)
            return

        # Identify remaining targets
        remaining_targets = [cell for cell in self.target_shape if not self.cells[cell]["active"]]
        if not remaining_targets and not self.moving_cells:
            self.finish_movement(success=True)
            return

        # Start new movements for all available active cells
        if remaining_targets and self.active_cells:
            self.start_new_movements(remaining_targets)

        # Continue the movement process
        self.movement_timer = self.root.after(50, self.process_parallel_movements)

    def start_new_movements(self, remaining_targets):
        """
        Start new movements for active cells with improved prioritization to ensure
        full shape filling, especially problematic cells like row 5, column 4 in circle.
        """
        # Get active cells that aren't already moving
        available_active_cells = [
            cell for cell in self.active_cells
            if cell not in [info[3] for info in self.moving_cells.values() if len(info) > 3]
        ]

        if not available_active_cells or not remaining_targets:
            return

        # Create a special priority list - cells that have been 'stuck' and
        # need special attention (like the problematic cell at (5,4))
        priority_targets = []
        for target in remaining_targets:
            # Check if this is one of our problematic cells
            row, col = target
            # Specifically prioritize cells that are typically problematic in the circle
            if (row == 5 and col == 4) or (row == 4 and col == 5) or (row == 4 and col == 4) or (row == 5 and col == 5):
                priority_targets.append(target)
            # Also prioritize any cell that has surrounding filled cells
            filled_neighbors = 0
            for neighbor in self.get_neighbors(target):
                if neighbor in self.target_shape and self.cells[neighbor]["active"]:
                    filled_neighbors += 1
            # If a cell has 3+ filled neighbors, it might be getting trapped
            if filled_neighbors >= 3:
                priority_targets.append(target)

        # Map to track which cells will be used by new paths
        newly_reserved_cells = set()

        # List of movements to actually start after planning
        movements_to_start = []

        # First handle priority targets
        if priority_targets and available_active_cells:
            self.update_status(f"Handling {len(priority_targets)} priority targets")
            # Sort active cells by distance to priority targets
            sorted_active_cells = sorted(
                available_active_cells,
                key=lambda cell: min([math.dist(cell, target) for target in priority_targets])
            )

            # Try to assign active cells to priority targets first
            for priority_target in priority_targets:
                if priority_target not in remaining_targets:
                    continue

                # Find closest active cell that can reach this target
                best_path = None
                best_active = None
                for active_cell in sorted_active_cells[:]:  # Make a copy to allow removal
                    path = self.find_path(active_cell, priority_target)
                    if path:
                        # Check path conflicts
                        conflict = False
                        for step in path:
                            if step in newly_reserved_cells:
                                conflict = True
                                break

                        if not conflict:
                            best_path = path
                            best_active = active_cell
                            break

                if best_path and best_active:
                    # Reserve path
                    for step in best_path:
                        newly_reserved_cells.add(step)

                    # Add movement
                    movements_to_start.append((best_active, priority_target, best_path))

                    # Remove from consideration
                    if best_active in sorted_active_cells:
                        sorted_active_cells.remove(best_active)
                        available_active_cells.remove(best_active)
                    remaining_targets.remove(priority_target)

                    # Update tracking
                    if priority_target not in self.path_attempts:
                        self.path_attempts[priority_target] = 0
                    self.path_attempts[priority_target] += 1

        # Process remaining targets normally
        # Sort active cells by distance to any target
        if remaining_targets:
            sorted_active_cells = sorted(
                available_active_cells,
                key=lambda cell: min([math.dist(cell, target) for target in remaining_targets])
            )
        else:
            # If no remaining targets, just use the original order
            sorted_active_cells = available_active_cells.copy()

        # Process cells in sorted order
        for active_cell in sorted_active_cells:
            # Skip if we've used all targets
            if not remaining_targets:
                break

            # Calculate target costs excluding newly reserved paths
            target_costs = {}
            for target in remaining_targets:
                # Skip targets that have been attempted too many times
                if target in self.path_attempts and self.path_attempts[target] >= self.max_attempts:
                    continue

                path = self.find_path(active_cell, target)
                if path:
                    # Check if path conflicts with newly reserved cells
                    conflict = False
                    for step in path:
                        if step in newly_reserved_cells:
                            conflict = True
                            break

                    if not conflict:
                        target_costs[target] = len(path)

            if not target_costs:
                continue  # No available targets for this cell

            # Select the best target (prioritize shortest paths for remaining cells)
            best_target = min(target_costs, key=lambda k: target_costs[k])
            path = self.find_path(active_cell, best_target)

            if path:
                # Reserve all cells in this path
                for step in path:
                    newly_reserved_cells.add(step)

                # Track this movement
                movements_to_start.append((active_cell, best_target, path))

                # Remove this target from consideration
                remaining_targets.remove(best_target)

                # Increment attempt counter
                if best_target not in self.path_attempts:
                    self.path_attempts[best_target] = 0
                self.path_attempts[best_target] += 1

        # Now actually start all the planned movements
        for active_cell, target, path in movements_to_start:
            # Remove cell from active cells
            self.active_cells.remove(active_cell)

            # Update metrics
            self.metrics[self.current_algorithm]["path_length"] += len(path)
            self.metrics[self.current_algorithm]["moves"] += 1

            # Reserve cells along the path
            self.reserve_cells(path)

            # Follow the path (animate movement)
            self.follow_path(path, active_cell, target)

    def update_moving_cells(self):
        """Update the position of all currently moving cells with synchronized movement."""
        # First pass - collect all planned moves and detect collisions
        completed_moves = []
        next_positions = {}
        collision_cells = set()

        for move_id, (path, index, target, start_cell) in self.moving_cells.items():
            if index >= len(path):
                completed_moves.append(move_id)
                continue

            next_pos = path[index]

            # If two cells would move to the same position, mark as collision
            if next_pos in next_positions:
                collision_cells.add(next_pos)
                # Mark both movements for deadlock increment
                self.deadlock_counter[move_id] = self.deadlock_counter.get(move_id, 0) + 1
                self.deadlock_counter[next_positions[next_pos]] = self.deadlock_counter.get(next_positions[next_pos],
                                                                                            0) + 1
            else:
                next_positions[next_pos] = move_id

        # Second pass - collect all movements that will be executed
        moves_to_execute = []
        for move_id, (path, index, target, start_cell) in self.moving_cells.items():
            if index >= len(path) or move_id in completed_moves:
                continue

            next_pos = path[index]
            # Skip moves to collision cells
            if next_pos in collision_cells:
                self.deadlock_counter[move_id] = self.deadlock_counter.get(move_id, 0) + 1
                continue

            # Get current position
            prev_cell = path[index - 1] if index > 0 else start_cell

            # Add to execution list
            moves_to_execute.append((move_id, prev_cell, next_pos))

            # Move to next step in path
            self.moving_cells[move_id] = (path, index + 1, target, start_cell)

            # Reset deadlock counter since movement happened
            self.deadlock_counter[move_id] = 0

        # Third pass - execute all valid moves at once
        # First deactivate all previous positions
        for move_id, prev_cell, next_pos in moves_to_execute:
            self.deactivate_cell(prev_cell)
            self.unreserve_cell(prev_cell)

        # Then activate all new positions
        for move_id, prev_cell, next_pos in moves_to_execute:
            self.activate_cell(next_pos)

        # Process completed movements
        for move_id in completed_moves:
            if move_id in self.moving_cells:
                path, index, target, start_cell = self.moving_cells[move_id]

                # Activate the target cell
                self.activate_cell(target)
                self.cells[target]["active"] = True
                self.unreserve_cell(target)

                # Clear attempt counter for this target
                if target in self.path_attempts:
                    del self.path_attempts[target]

                # Increment filled cells counter
                self.cells_filled += 1

                # Update metrics display
                self.update_metrics_display()

                # Remove from tracking
                if move_id in self.deadlock_counter:
                    del self.deadlock_counter[move_id]
                del self.moving_cells[move_id]

    def finish_movement(self, success):
        """Handle the end of all movements."""
        elapsed_time = time.time() - self.start_time

        # Verify agent count if we're in queue mode
        if hasattr(self, 'queue_agent_count') and hasattr(self, 'queue_positions'):
            active_agent_count = 0
            for cell in self.cells:
                if self.cells[cell]["active"]:
                    active_agent_count += 1

            expected_agent_count = self.queue_agent_count

            # If we've lost agents, just log it but don't try to recover them
            if active_agent_count < expected_agent_count:
                agents_lost = expected_agent_count - active_agent_count
                self.update_status(f"WARNING: {agents_lost} agents were lost during movement. Active: {active_agent_count}, Expected: {expected_agent_count}")

                # Update the queue agent count to match the actual count
                self.queue_agent_count = active_agent_count
                self.update_status("Continuing with the remaining agents without recovery")

        if success:
            self.update_status(f"Target shape formation complete in {elapsed_time:.2f}s!")
            self.metrics[self.current_algorithm]["success"] += 1
        else:
            self.update_status("Movement failed: No more active cells available.")
            self.metrics[self.current_algorithm]["failures"] += 1

        self.metrics[self.current_algorithm]["time"] += elapsed_time
        self.update_metrics_display()

        self.movement_started = False
        self.do_shape_btn.config(state=tk.NORMAL)

        # Cancel any pending timer
        if self.movement_timer:
            self.root.after_cancel(self.movement_timer)
            self.movement_timer = None

        # Clean up queue-related variables
        if hasattr(self, 'queue_positions'):
            del self.queue_positions
        if hasattr(self, 'queue_completed'):
            del self.queue_completed
        if hasattr(self, 'position_history'):
            del self.position_history

    def reshape(self, shape_type):
        """Handle reshaping from one shape to another without resetting."""
        # Cancel any pending movement timer
        if self.movement_timer:
            self.root.after_cancel(self.movement_timer)
            self.movement_timer = None

        # Count how many agents we should have
        expected_agent_count = self.agent_count
        self.update_status(f"Expected agent count: {expected_agent_count}")

        # Get all current active cells (agents)
        current_active_cells = []

        # First, collect all cells that are part of the current shape
        current_shape_cells = []
        for cell in self.cells:
            if self.cells[cell]["active"]:
                current_shape_cells.append(cell)

        self.update_status(f"Found {len(current_shape_cells)} cells in the current shape.")

        # Include cells that are in the middle of movement
        moving_cells = []
        for move_id, (path, index, target, start_cell) in self.moving_cells.items():
            # Get current position of moving cell
            current_pos = path[index - 1] if index > 0 else start_cell
            if current_pos not in moving_cells:
                moving_cells.append(current_pos)

        self.update_status(f"Found {len(moving_cells)} cells that are currently moving.")

        # Combine all cells
        for cell in current_shape_cells:
            if cell not in current_active_cells:
                current_active_cells.append(cell)

        for cell in moving_cells:
            if cell not in current_active_cells:
                current_active_cells.append(cell)

        # Check if we have the expected number of agents
        if len(current_active_cells) < expected_agent_count:
            self.update_status(f"Warning: Found only {len(current_active_cells)} agents, expected {expected_agent_count}.")

            # If we don't have enough agents, we need to recreate them
            # First, let's check if we need to add more agents
            if len(current_active_cells) < expected_agent_count:
                # We need to add more agents
                agents_to_add = expected_agent_count - len(current_active_cells)
                self.update_status(f"Adding {agents_to_add} new agents.")

                # Find empty cells that are not in the target shape or obstacles
                empty_cells = []
                for cell in self.cells:
                    if (not self.cells[cell]["active"] and
                        not self.cells[cell]["obstacle"] and
                        cell not in self.target_shape and
                        cell not in current_active_cells):
                        empty_cells.append(cell)

                # Add new agents
                for i in range(min(agents_to_add, len(empty_cells))):
                    current_active_cells.append(empty_cells[i])

        # Store the current active cells before deactivating them
        self.update_status(f"Preparing to reshape with {len(current_active_cells)} agents.")

        # Deactivate all cells in the grid
        for cell in self.cells:
            if self.cells[cell]["active"]:
                # Deactivate the cell in the grid
                self.cells[cell]["active"] = False
                self.canvas.itemconfig(self.cells[cell]["rect"], fill=INACTIVE_COLOR)

        # Clear movement-related data structures
        self.moving_cells = {}
        self.deadlock_counter = {}
        self.path_attempts = {}
        self.reserved_cells = set()

        # Update the target shape based on the shape type
        self.remove_green_outline()
        if shape_type == "rectangle":
            self.target_shape = self.define_target_rectangle()
            shape_name = "rectangle"
        elif shape_type == "triangle":
            self.target_shape = self.define_target_triangle()
            shape_name = "triangle"
        elif shape_type == "circle":
            self.target_shape = self.define_target_circle()
            shape_name = "circle"
        elif shape_type == "custom":
            # Use the existing custom shape
            self.target_shape = self.custom_shape.copy()
            shape_name = "custom shape"
        else:
            # Default to rectangle if shape type is not recognized
            self.target_shape = self.define_target_rectangle()
            shape_name = "rectangle"

        # Update shape-related properties
        self.inner_cells, self.outline_cells, self.corner_cells = self.separate_cells()
        self.draw_green_outline()
        self.total_cells_to_fill = len(self.target_shape)

        # Update active cells
        self.active_cells = current_active_cells

        # Reset movement state
        self.movement_started = False

        # Make sure the "Do the Shape" button is enabled
        self.do_shape_btn.config(state=tk.NORMAL)

        # Update status
        self.update_status(f"Reshaping to {shape_name}. {len(current_active_cells)} agents available.")

        # Start the movement process
        self.start_movement()

        # Update AI assistant if visible
        try:
            if hasattr(self, 'ai_assistant') and self.ai_assistant.window.state() == 'normal':
                self.ai_assistant.display_message(
                    f"Reshaping to {shape_name}. The agents will now reorganize to form the new shape "
                    f"using the {self.current_algorithm} algorithm.",
                    "assistant")
        except:
            pass

    def detect_and_resolve_deadlocks(self):
        """Enhanced deadlock detection and resolution."""
        deadlocked_movements = []

        # Check for cells that haven't moved
        for move_id, (path, index, target, start_cell) in self.moving_cells.items():
            if move_id in self.deadlock_counter:
                self.deadlock_counter[move_id] += 1

                # If stuck for too long (shorter time than before)
                if self.deadlock_counter[move_id] > 10:  # About 0.5 seconds
                    deadlocked_movements.append(move_id)

        # If more than 30% of movements are deadlocked, do a major reset
        if deadlocked_movements and len(deadlocked_movements) > 0.3 * len(self.moving_cells):
            self.update_status("Major deadlock detected, resetting all movements")

            # Reset all movements
            for move_id in list(self.moving_cells.keys()):
                self.abort_movement(move_id)

            # Clear all reservations to start fresh
            self.reserved_cells.clear()
        else:
            # Just abort individual deadlocked movements
            for move_id in deadlocked_movements:
                self.update_status(f"Resetting stuck movement {move_id}")
                self.abort_movement(move_id)

    def abort_movement(self, move_id):
        """Abort a movement and return the cell to available active cells."""
        if move_id not in self.moving_cells:
            return

        path, index, target, start_cell = self.moving_cells[move_id]

        # Get current position
        current_pos = path[index - 1] if index > 0 else start_cell

        # Unreserve path
        for cell in path[index:]:
            self.unreserve_cell(cell)

        # Return cell to active cells
        self.active_cells.append(current_pos)

        # Remove from moving cells
        del self.moving_cells[move_id]
        if move_id in self.deadlock_counter:
            del self.deadlock_counter[move_id]

    def move_next_square(self):
        """Core movement logic with dynamic hardest-target selection."""
        if not self.active_cells:
            elapsed_time = time.time() - self.start_time
            self.update_status("No more active cells available.")

            # Calculate success rate based on completed targets
            remaining_targets = [cell for cell in self.target_shape if not self.cells[cell]["active"]]
            completed_targets = len(self.target_shape) - len(remaining_targets)
            total_targets = len(self.target_shape)
            success_rate = (1 - (len(remaining_targets) / total_targets)) * 100 if total_targets > 0 else 0

            # Update metrics
            self.metrics[self.current_algorithm]["completed_targets"] = completed_targets
            self.metrics[self.current_algorithm]["total_targets"] = total_targets
            self.metrics[self.current_algorithm]["success_rate"] = success_rate
            self.metrics[self.current_algorithm]["time"] += elapsed_time
            self.update_metrics_display()

            self.movement_started = False
            self.do_shape_btn.config(state=tk.NORMAL)
            return

        remaining_targets = [cell for cell in self.target_shape if not self.cells[cell]["active"]]
        if not remaining_targets:
            elapsed_time = time.time() - self.start_time
            self.update_status(f"Target shape formation complete in {elapsed_time:.2f}s!")

            # All targets completed - 100% success rate
            total_targets = len(self.target_shape)

            # Update metrics
            self.metrics[self.current_algorithm]["completed_targets"] = total_targets
            self.metrics[self.current_algorithm]["total_targets"] = total_targets
            self.metrics[self.current_algorithm]["success_rate"] = 100.0
            self.metrics[self.current_algorithm]["time"] += elapsed_time
            self.update_metrics_display()

            self.movement_started = False
            self.do_shape_btn.config(state=tk.NORMAL)
            return

        # Calculate minimal path lengths for each target
        target_costs = {}
        for target in remaining_targets:
            min_length = float('inf')
            for active in self.active_cells:
                path = self.find_path(active, target)
                if path:
                    min_length = min(min_length, len(path))
            if min_length != float('inf'):
                target_costs[target] = min_length

        if not target_costs:
            elapsed_time = time.time() - self.start_time
            self.update_status("No reachable targets left")

            # Calculate success rate based on completed targets
            remaining_targets = [cell for cell in self.target_shape if not self.cells[cell]["active"]]
            completed_targets = len(self.target_shape) - len(remaining_targets)
            total_targets = len(self.target_shape)
            success_rate = (1 - (len(remaining_targets) / total_targets)) * 100 if total_targets > 0 else 0

            # Update metrics
            self.metrics[self.current_algorithm]["completed_targets"] = completed_targets
            self.metrics[self.current_algorithm]["total_targets"] = total_targets
            self.metrics[self.current_algorithm]["success_rate"] = success_rate
            self.metrics[self.current_algorithm]["time"] += elapsed_time
            self.update_metrics_display()

            self.movement_started = False
            self.do_shape_btn.config(state=tk.NORMAL)
            return

        # Select the hardest target (with the maximum minimal path length)
        hardest_target = max(target_costs, key=lambda k: target_costs[k])

        # Find the active cell with the shortest path to the hardest target
        shortest_path = None
        shortest_length = float('inf')
        selected_active = None

        for active in self.active_cells:
            path = self.find_path(active, hardest_target)
            if path and len(path) < shortest_length:
                shortest_length = len(path)
                shortest_path = path
                selected_active = active

        if not selected_active:
            self.root.after(50, self.move_next_square)
            return

        self.active_cells.remove(selected_active)

        if shortest_path:
            # Update path length metric
            self.metrics[self.current_algorithm]["path_length"] += len(shortest_path)
            self.metrics[self.current_algorithm]["moves"] += 1

            self.reserve_cells(shortest_path)
            self.follow_path(shortest_path, selected_active, hardest_target)
        else:
            self.active_cells.append(selected_active)
            self.root.after(500, self.move_next_square)

    def find_path(self, start, goal):
        """Find path using the selected algorithm."""
        algorithm = self.current_algorithm

        # Clear previous visited cells visualization
        self.clear_visited_cells()

        # Start timing
        start_time = time.time()

        if algorithm == "A*":
            path, explored_count = self.a_star(start, goal)
        elif algorithm == "BFS":
            path, explored_count = self.bfs_search(start, goal)
        elif algorithm == "DFS":
            path, explored_count = self.dfs_search(start, goal)
        elif algorithm == "Minimax":
            path, explored_count = self.minimax_pathfinding(start, goal)
        elif algorithm == "Alpha-Beta":
            path, explored_count = self.alpha_beta_pathfinding(start, goal)
        elif algorithm == "Expectimax":
            path, explored_count = self.expectimax_pathfinding(start, goal)
        else:
            # Default to A*
            path, explored_count = self.a_star(start, goal)

        # Calculate time taken
        elapsed_time = time.time() - start_time

        # Update metrics
        self.metrics[algorithm]["time"] += elapsed_time
        self.metrics[algorithm]["explored"] += explored_count

        # We no longer track individual pathfinding success/failure

        return path

    def a_star(self, start, goal):
        """A* pathfinding implementation with obstacle avoidance."""
        explored_count = 0

        def heuristic(a, b):
            return math.dist(a, b)

        open_set = []
        heapq.heappush(open_set, (0, start))
        g_score = {start: 0}
        came_from = {}

        while open_set:
            _, current = heapq.heappop(open_set)
            explored_count += 1

            # Mark as visited (for visualization)
            if current != start and current != goal:
                self.mark_visited(current)

            if current == goal:
                # Reconstruct path
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.append(start)
                return path[::-1], explored_count

            for neighbor in self.get_neighbors(current):
                if (self.cells[neighbor]["obstacle"] or
                        self.cells[neighbor]["active"] or
                        neighbor in self.reserved_cells):
                    continue

                move_cost = 1 if abs(neighbor[0] - current[0]) + abs(neighbor[1] - current[1]) == 1 else math.sqrt(2)
                tentative_g_score = g_score.get(current, float('inf')) + move_cost

                if tentative_g_score < g_score.get(neighbor, float('inf')):
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g_score
                    f_score = tentative_g_score + heuristic(neighbor, goal)
                    heapq.heappush(open_set, (f_score, neighbor))

        return None, explored_count

    def bfs_search(self, start, goal):
        """Breadth-First Search implementation."""
        explored_count = 0

        queue = deque([[start]])
        visited = {start}

        while queue:
            path = queue.popleft()
            current = path[-1]
            explored_count += 1

            # Mark as visited (for visualization)
            if current != start and current != goal:
                self.mark_visited(current)

            if current == goal:
                return path, explored_count

            for neighbor in self.get_neighbors(current):
                if (neighbor in visited or
                        self.cells[neighbor]["obstacle"] or
                        self.cells[neighbor]["active"] or
                        neighbor in self.reserved_cells):
                    continue

                visited.add(neighbor)
                new_path = list(path)
                new_path.append(neighbor)
                queue.append(new_path)

        return None, explored_count

    def dfs_search(self, start, goal):
        """Depth-First Search implementation."""
        explored_count = 0

        stack = [[start]]
        visited = {start}

        while stack:
            path = stack.pop()
            current = path[-1]
            explored_count += 1

            # Mark as visited (for visualization)
            if current != start and current != goal:
                self.mark_visited(current)

            if current == goal:
                return path, explored_count

            # Reverse neighbors to maintain a more natural DFS order
            neighbors = list(self.get_neighbors(current))
            neighbors.reverse()

            for neighbor in neighbors:
                if (neighbor in visited or
                        self.cells[neighbor]["obstacle"] or
                        self.cells[neighbor]["active"] or
                        neighbor in self.reserved_cells):
                    continue

                visited.add(neighbor)
                new_path = list(path)
                new_path.append(neighbor)
                stack.append(new_path)

        return None, explored_count

    def minimax_pathfinding(self, start, goal):
        """
        Minimax algorithm adapted for pathfinding.

        In this adaptation:
        - The agent tries to maximize its position (closer to goal)
        - The "opponent" (environment) tries to minimize (force longer paths)
        - We use a depth limit to prevent excessive exploration
        - We return the best path found within the depth limit
        """
        start_time = time.time()
        explored_count = 0
        max_depth = 5  # Reduced depth to prevent freezing
        max_explored = 500  # Limit the number of nodes to explore
        timeout = 1.0  # Timeout in seconds

        # Calculate heuristic distance (Manhattan distance)
        def heuristic(pos):
            return abs(pos[0] - goal[0]) + abs(pos[1] - goal[1])

        # Minimax function with alpha-beta pruning
        def minimax(position, depth, alpha, beta, maximizing_player, path):
            nonlocal explored_count
            explored_count += 1

            # Early termination if we've explored too many nodes or exceeded timeout
            if explored_count > max_explored or (time.time() - start_time) > timeout:
                return -heuristic(position), path + [position]

            # Mark as visited for visualization (limit visualization to prevent UI freezing)
            if position != start and position != goal and explored_count % 10 == 0:
                self.mark_visited(position)

            # Base cases
            if position == goal:
                return float('inf'), path + [position]

            if depth == 0:
                # Return negative heuristic as score (closer to goal = higher score)
                return -heuristic(position), path + [position]

            # Get valid neighbors
            neighbors = []
            for neighbor in self.get_neighbors(position):
                if (self.cells[neighbor]["obstacle"] or
                    self.cells[neighbor]["active"] or
                    neighbor in self.reserved_cells or
                    neighbor in path):  # Avoid cycles
                    continue
                neighbors.append(neighbor)

            # If no valid moves, return a poor score
            if not neighbors:
                return float('-inf') if maximizing_player else float('inf'), path

            if maximizing_player:
                # Sort neighbors by heuristic to improve pruning
                neighbors.sort(key=lambda n: heuristic(n))

                best_score = float('-inf')
                best_path = path

                for neighbor in neighbors:
                    score, new_path = minimax(neighbor, depth - 1, alpha, beta, False, path + [position])

                    if score > best_score:
                        best_score = score
                        best_path = new_path

                    alpha = max(alpha, best_score)
                    if beta <= alpha:
                        break

                return best_score, best_path
            else:
                # Sort neighbors by heuristic (reversed) to improve pruning
                neighbors.sort(key=lambda n: -heuristic(n))

                best_score = float('inf')
                best_path = path

                for neighbor in neighbors:
                    score, new_path = minimax(neighbor, depth - 1, alpha, beta, True, path + [position])

                    if score < best_score:
                        best_score = score
                        best_path = new_path

                    beta = min(beta, best_score)
                    if beta <= alpha:
                        break

                return best_score, best_path

        # Start minimax search with timeout protection
        try:
            _, path = minimax(start, max_depth, float('-inf'), float('inf'), True, [])

            # If search took too long, fall back to A*
            if (time.time() - start_time) > timeout:
                self.update_status("Minimax timeout - falling back to A*")
                a_star_path, a_star_explored = self.a_star(start, goal)
                explored_count += a_star_explored
                return a_star_path, explored_count
        except Exception as e:
            self.update_status(f"Minimax error: {str(e)} - falling back to A*")
            a_star_path, a_star_explored = self.a_star(start, goal)
            explored_count += a_star_explored
            return a_star_path, explored_count

        # Clean up the path (remove duplicates and ensure it starts with start)
        if path and path[0] != start:
            path = [start] + path

        # Check if path reaches the goal
        if not path or path[-1] != goal:
            # If goal not reached, try A* as fallback
            a_star_path, a_star_explored = self.a_star(start, goal)
            explored_count += a_star_explored
            return a_star_path, explored_count

        return path, explored_count

    def get_neighbors(self, cell):
        """Returns valid neighbor cells with diagonal moves allowed only if adjacent cells are free."""
        row, col = cell
        neighbors = []

        # Cardinal moves
        cardinal_moves = [
            (row - 1, col), (row + 1, col),
            (row, col - 1), (row, col + 1)
        ]

        for r, c in cardinal_moves:
            if 0 <= r < self.grid_size and 0 <= c < self.grid_size:
                neighbors.append((r, c))

        # Diagonal moves (only allowed if adjacent cardinal cells are free)
        diagonal_moves = [
            (row - 1, col - 1), (row - 1, col + 1),
            (row + 1, col - 1), (row + 1, col + 1)
        ]

        for i, (r, c) in enumerate(diagonal_moves):
            if 0 <= r < self.grid_size and 0 <= c < self.grid_size:
                # Check if the adjacent cardinal cells are free
                if i == 0:  # NW
                    adj1, adj2 = (row - 1, col), (row, col - 1)
                elif i == 1:  # NE
                    adj1, adj2 = (row - 1, col), (row, col + 1)
                elif i == 2:  # SW
                    adj1, adj2 = (row + 1, col), (row, col - 1)
                else:  # SE
                    adj1, adj2 = (row + 1, col), (row, col + 1)

                # Allow diagonal moves only if both adjacent cells are valid and not obstacles
                if (0 <= adj1[0] < self.grid_size and 0 <= adj1[1] < self.grid_size and
                        0 <= adj2[0] < self.grid_size and 0 <= adj2[1] < self.grid_size and
                        not self.cells[adj1]["obstacle"] and
                        not self.cells[adj2]["obstacle"]):
                    neighbors.append((r, c))

        return neighbors

    def mark_visited(self, cell):
        """Mark a cell as visited during search (for visualization)."""
        self.visited_cells.add(cell)


    def clear_visited_cells(self):
        """Clear visualization of visited cells."""
        self.visited_cells.clear()

    def reserve_cells(self, path):
        """Reserves cells along the given path to prevent collisions."""
        for cell in path:
            self.reserved_cells.add(cell)

    def unreserve_cell(self, cell):
        """Clears a cell's reservation."""
        if cell in self.reserved_cells:
            self.reserved_cells.remove(cell)

    def follow_path(self, path, current_cell, target_cell):
        """Animates the movement of a cell along the given path."""

        def move_step(index, prev=None):
            if index >= len(path):
                self.activate_cell(target_cell)
                self.cells[target_cell]["active"] = True
                self.unreserve_cell(target_cell)

                # Increment filled cells counter
                self.cells_filled += 1

                # Update metrics display
                self.update_metrics_display()

                self.root.after(self.movement_speed, self.move_next_square)
                return

            cell = path[index]
            if prev:
                self.deactivate_cell(prev)
                self.unreserve_cell(prev)
            self.activate_cell(cell)
            self.root.after(self.movement_speed, lambda: move_step(index + 1, cell))

        self.deactivate_cell(current_cell)
        move_step(0, current_cell)

    def deactivate_cell(self, cell):
        """Deactivates a cell visually."""
        row, col = cell
        self.canvas.itemconfig(self.cells[(row, col)]["rect"], fill=INACTIVE_COLOR)
        self.cells[(row, col)]["active"] = False

    def activate_cell(self, cell):
        """Activates a cell visually."""
        row, col = cell
        self.canvas.itemconfig(self.cells[(row, col)]["rect"], fill=ACTIVE_COLOR)
        self.cells[(row, col)]["active"] = True

    def compare_algorithms(self):
        """Run comparison tests for all algorithms on the current configuration."""
        if self.movement_started:
            self.update_status("Cannot compare while movement is in progress.")
            return

        # Save current grid state
        saved_cells = {}
        for cell in self.cells:
            saved_cells[cell] = self.cells[cell].copy()
        saved_active_cells = self.active_cells.copy()
        saved_shape = self.target_shape.copy()

        # Save current algorithm
        saved_algorithm = self.current_algorithm

        # Save current metrics
        saved_metrics = {}
        for algo, metrics in self.metrics.items():
            saved_metrics[algo] = metrics.copy()

        algorithms = ["A*", "BFS", "DFS", "Minimax", "Alpha-Beta", "Expectimax"]
        comparison_results = {}

        for algo in algorithms:
            # Reset grid to saved state
            self.reset_comparison_grid(saved_cells, saved_active_cells, saved_shape)

            # Set algorithm
            self.current_algorithm = algo
            self.algorithm_var.set(algo)

            # Reset metrics for this algorithm for the comparison
            self.metrics[algo] = {
                "explored": 0,
                "path_length": 0,
                "time": 0,
                "moves": 0,
                "success_rate": 0,
                "completed_targets": 0,
                "total_targets": 0
            }

            # Add special metrics for specific algorithms
            if algo == "Alpha-Beta":
                self.metrics[algo]["pruned"] = 0
            elif algo == "Expectimax":
                self.metrics[algo]["chance_nodes"] = 0

            # Run simulation
            start_time = time.time()
            success, stats = self.run_simulation_batch()
            total_time = time.time() - start_time

            comparison_results[algo] = {
                "success": success,
                "time": total_time,
                "stats": stats
            }

            # Update display
            self.update_status(f"Algorithm {algo}: {'Success' if success else 'Failed'} - {total_time:.2f}s")

        # Generate comparison report
        self.generate_comparison_report(comparison_results)

        # Reset to original state
        self.reset_comparison_grid(saved_cells, saved_active_cells, saved_shape)

        # Restore original algorithm
        self.current_algorithm = saved_algorithm
        self.algorithm_var.set(saved_algorithm)

        # Restore original metrics
        self.metrics = saved_metrics

        # Update metrics display
        self.update_metrics_display()

    def reset_comparison_grid(self, saved_cells, saved_active_cells, saved_shape):
        """Reset grid to a saved state for comparison tests."""
        # Clear canvas
        self.canvas.delete("all")

        # Restore cells
        self.cells = {}
        for cell, properties in saved_cells.items():
            row, col = cell
            x1, y1 = col * self.cell_size, row * self.cell_size
            x2, y2 = x1 + self.cell_size, y1 + self.cell_size

            fill_color = ACTIVE_COLOR if properties["active"] else INACTIVE_COLOR
            if properties["obstacle"]:
                fill_color = OBSTACLE_COLOR

            rect = self.canvas.create_rectangle(x1, y1, x2, y2, fill=fill_color, outline=GRID_COLOR)

            self.cells[cell] = properties.copy()
            self.cells[cell]["rect"] = rect

        # Restore active cells
        self.active_cells = saved_active_cells.copy()

        # Restore target shape
        self.target_shape = saved_shape.copy()
        self.draw_green_outline()

        # Reset other state
        self.reserved_cells = set()
        self.visited_cells = set()
        self.cells_filled = 0
        self.movement_started = False

    def run_simulation_batch(self):
        """Run a complete simulation without animation for quick comparison."""
        # Set up for simulation
        self.movement_started = True
        self.cells_filled = 0

        # Start time for the entire simulation
        self.sim_start_time = time.time()

    def start_parallel_centralized_movement(self):
        """
        Start the worm-like movement pattern (F1 safety car queue) with decentralized decision making:
        1. Each agent independently selects its own target
        2. Agents still move in a queue formation (following the agent ahead)
        3. The queue structure is maintained but decisions are decentralized
        """
        self.update_status("Starting decentralized F1 safety car queue movement pattern")

        # Step 1: Scan all orange cells and all free target cells
        active_cells = self.active_cells.copy()
        remaining_targets = [cell for cell in self.target_shape if not self.cells[cell]["active"]]

        if not remaining_targets:
            self.finish_movement(success=True)
            return

        if not active_cells:
            self.finish_movement(success=False)
            return

        # In decentralized mode, each agent selects its own target based on proximity
        # We'll still maintain a queue structure, but each agent makes its own decision

        # Step 2: Create the queue structure
        self.queue_assignments = []

        # First, select a leader (head) for the queue
        # We'll use the cell that is closest to any target
        best_head_cell = None
        min_distance = float('inf')

        for cell in active_cells:
            for target in remaining_targets:
                distance = math.dist(cell, target)
                if distance < min_distance:
                    min_distance = distance
                    best_head_cell = cell

        if not best_head_cell:
            self.update_status("No suitable head cell found")
            self.finish_movement(success=False)
            return

        self.update_status(f"Selected head cell: {best_head_cell}")

        # Now, each agent independently selects its own target based on proximity
        # The head selects first
        head_target = None
        min_distance = float('inf')
        head_path = None

        for target in remaining_targets:
            distance = math.dist(best_head_cell, target)
            path = self.find_path(best_head_cell, target)
            if path and distance < min_distance:
                min_distance = distance
                head_target = target
                head_path = path

        if not head_target:
            self.update_status("Head cell cannot reach any target")
            self.finish_movement(success=False)
            return

        # Add the head to the queue
        self.queue_assignments.append((best_head_cell, head_target, head_path))

        # Remove the head's target from available targets
        remaining_targets = [t for t in remaining_targets if t != head_target]

        # Remove the head from active cells
        remaining_active_cells = [cell for cell in active_cells if cell != best_head_cell]

        # Sort remaining active cells by distance to the head
        # This ensures cells that are closer to the head are earlier in the queue
        sorted_active_cells = sorted(remaining_active_cells,
                                    key=lambda cell: math.dist(cell, best_head_cell))

        # Each remaining agent selects its own target based on proximity
        for active_cell in sorted_active_cells:
            # Find the closest available target for this agent
            best_target = None
            min_distance = float('inf')

            for target in remaining_targets:
                distance = math.dist(active_cell, target)
                if distance < min_distance:
                    min_distance = distance
                    best_target = target

            if best_target:
                # Add this agent to the queue with its selected target
                self.queue_assignments.append((active_cell, best_target, None))
                # Remove this target from available targets
                remaining_targets = [t for t in remaining_targets if t != best_target]
            else:
                # If no target is available, assign to a random target
                if remaining_targets:
                    random_target = remaining_targets[0]
                    self.queue_assignments.append((active_cell, random_target, None))
                    remaining_targets = remaining_targets[1:]
                else:
                    # If all targets are assigned, this agent will follow without a specific target
                    # It will just follow the queue
                    self.queue_assignments.append((active_cell, None, None))

        self.update_status(f"Worm created with {len(self.queue_assignments)} segments")

        # Initialize queue movement
        self.queue_leader_index = 0
        self.queue_positions = {cell: cell for cell, _, _ in self.queue_assignments}
        self.queue_completed = set()

        # Keep track of the total number of agents for verification
        self.queue_agent_count = len(self.queue_assignments)
        self.update_status(f"Total agents in queue: {self.queue_agent_count}")

        # Initialize position history for queue movement
        self.position_history = {}
        for cell, _, _ in self.queue_assignments:
            self.position_history[cell] = [self.queue_positions[cell]]

        # Create a backup of active cells for recovery if needed
        self.queue_active_cells_backup = self.active_cells.copy()

        # Start the worm movement
        self.movement_timer = self.root.after(50, self.process_queue_movement)

    def process_queue_movement(self):
        """
        Process the decentralized F1 safety car queue movement where:
        1. The head moves along its path to its selected target
        2. Each segment follows the segment ahead of it, but has its own target
        3. Agents make independent decisions but maintain the queue formation
        """
        # Verify that we haven't lost any agents
        active_agent_count = 0
        for cell in self.cells:
            if self.cells[cell]["active"]:
                active_agent_count += 1

        completed_agent_count = len(self.queue_completed)
        expected_agent_count = self.queue_agent_count

        # If we've lost agents, log it and update the expected count
        if active_agent_count + completed_agent_count < expected_agent_count:
            agents_lost = expected_agent_count - (active_agent_count + completed_agent_count)
            self.update_status(f"WARNING: {agents_lost} agents were lost! Active: {active_agent_count}, Completed: {completed_agent_count}, Expected: {expected_agent_count}")

            # Update the expected count to match reality
            self.queue_agent_count = active_agent_count + completed_agent_count
            self.update_status("Continuing with the remaining agents without recovery")

        # Check if we're done
        if len(self.queue_completed) == len(self.queue_assignments):
            self.finish_movement(success=True)
            return

        # Get all cells that haven't reached their targets yet
        active_queue_cells = [(i, cell, target, path) for i, (cell, target, path) in enumerate(self.queue_assignments)
                             if cell not in self.queue_completed]

        if not active_queue_cells:
            self.finish_movement(success=True)
            return

        # Get the head of the worm (first cell in the queue)
        head_idx, head_cell, head_target, head_path = active_queue_cells[0]

        # Store the head's current position
        current_head_pos = self.queue_positions[head_cell]

        # If head's path is not set or needs recalculation, calculate it
        if not head_path:
            head_path = self.find_path(current_head_pos, head_target)
            self.queue_assignments[head_idx] = (head_cell, head_target, head_path)

            # If no path found, mark as completed and select new head
            if not head_path:
                self.queue_completed.add(head_cell)
                self.movement_timer = self.root.after(self.movement_speed, self.process_queue_movement)
                return

        # Move the head first
        if len(head_path) > 0:
            next_head_pos = head_path[0]

            # Debug output
            self.update_status(f"Moving worm head from {current_head_pos} to {next_head_pos}")

            # Move the head
            self.move_cell_animation(head_cell, current_head_pos, next_head_pos)

            # Update the head's position
            self.queue_positions[head_cell] = next_head_pos

            # Add the new position to the head's history
            self.position_history[head_cell].append(next_head_pos)

            # Keep history at a reasonable length
            if len(self.position_history[head_cell]) > 100:
                self.position_history[head_cell] = self.position_history[head_cell][-100:]

            # Update the head's path for next time
            self.queue_assignments[head_idx] = (
                head_cell,
                head_target,
                head_path[1:] if len(head_path) > 1 else []
            )

            # If head reached target, mark as completed
            if next_head_pos == head_target:
                self.queue_completed.add(head_cell)
                self.cells[next_head_pos]["active"] = True
                self.cells_filled += 1
                self.update_metrics_display()

                # If the head has completed, we need to promote the next cell to head
                if len(active_queue_cells) > 1:
                    next_head_idx, next_head_cell, next_head_target, _ = active_queue_cells[1]
                    # Calculate path for the new head
                    next_head_path = self.find_path(self.queue_positions[next_head_cell], next_head_target)
                    self.queue_assignments[next_head_idx] = (next_head_cell, next_head_target, next_head_path)

        # Now move each segment of the worm to follow the segment ahead of it
        for i in range(1, len(active_queue_cells)):
            _, follower_cell, follower_target, _ = active_queue_cells[i]

            # Get current position of this segment
            current_pos = self.queue_positions[follower_cell]

            # Get the cell ahead in the worm
            cell_ahead = active_queue_cells[i-1][1]

            # Get the previous position of the cell ahead (where it just moved from)
            if len(self.position_history[cell_ahead]) >= 2:
                # The position before the current one is where the cell ahead just moved from
                prev_ahead_pos = self.position_history[cell_ahead][-2]

                # Check if the follower can move to this position
                is_valid = (
                    not self.cells[prev_ahead_pos]["obstacle"] and
                    not self.cells[prev_ahead_pos]["active"] and
                    prev_ahead_pos != current_pos and  # Don't stay in place
                    prev_ahead_pos not in [self.queue_positions[c] for c, _, _ in self.queue_assignments
                                          if c != follower_cell and c not in self.queue_completed]
                )

                if is_valid:
                    # Debug output
                    self.update_status(f"Moving worm segment from {current_pos} to {prev_ahead_pos}")

                    # Move the follower to where the cell ahead just was
                    self.move_cell_animation(follower_cell, current_pos, prev_ahead_pos)
                    self.queue_positions[follower_cell] = prev_ahead_pos

                    # Add the new position to the follower's history
                    self.position_history[follower_cell].append(prev_ahead_pos)

                    # Keep history at a reasonable length
                    if len(self.position_history[follower_cell]) > 100:
                        self.position_history[follower_cell] = self.position_history[follower_cell][-100:]

                    # If follower reached target, mark as completed
                    if prev_ahead_pos == follower_target:
                        self.queue_completed.add(follower_cell)
                        self.cells[prev_ahead_pos]["active"] = True
                        self.cells_filled += 1
                        self.update_metrics_display()

        # Continue the movement
        self.movement_timer = self.root.after(self.movement_speed, self.process_queue_movement)

    def move_cell_animation(self, cell_id, from_pos, to_pos):
        """
        Animate a cell moving from one position to another.

        Args:
            cell_id: The cell identifier (used for tracking)
            from_pos: The position to move from
            to_pos: The position to move to
        """
        # Verify positions are valid
        if from_pos not in self.cells or to_pos not in self.cells:
            self.update_status(f"WARNING: Invalid position in move_cell_animation: from={from_pos}, to={to_pos}")
            return

        # Check if the target position is already active (occupied by another agent)
        if self.cells[to_pos]["active"] and to_pos != from_pos:
            self.update_status(f"WARNING: Target position {to_pos} is already active!")

        # Deactivate the previous position
        if from_pos in self.cells:
            self.cells[from_pos]["active"] = False
            self.canvas.itemconfig(self.cells[from_pos]["rect"], fill=INACTIVE_COLOR)

        # Activate the new position
        if to_pos in self.cells:
            self.cells[to_pos]["active"] = True
            self.canvas.itemconfig(self.cells[to_pos]["rect"], fill=ACTIVE_COLOR)

        # Update the position in our tracking dictionaries
        if hasattr(self, 'queue_positions') and cell_id in self.queue_positions:
            self.queue_positions[cell_id] = to_pos

    def find_path_batch(self, start, goal):
        """Fast pathfinding version without visualization for batch testing."""
        algorithm = self.current_algorithm

        # Get the path and explored count
        if algorithm == "A*":
            path, explored_count = self.a_star_batch(start, goal)
        elif algorithm == "BFS":
            path, explored_count = self.bfs_search_batch(start, goal)
        elif algorithm == "DFS":
            path, explored_count = self.dfs_search_batch(start, goal)
        elif algorithm == "Minimax":
            path, explored_count = self.minimax_pathfinding_batch(start, goal)
        elif algorithm == "Alpha-Beta":
            path, explored_count = self.alpha_beta_pathfinding_batch(start, goal)
        elif algorithm == "Expectimax":
            path, explored_count = self.expectimax_pathfinding_batch(start, goal)
        else:
            # Default to A*
            path, explored_count = self.a_star_batch(start, goal)

        # We no longer track individual pathfinding success/failure

        return path, explored_count

    def a_star_batch(self, start, goal):
        """A* implementation for batch testing (no visualization)."""
        explored_count = 0

        def heuristic(a, b):
            return math.dist(a, b)

        open_set = []
        heapq.heappush(open_set, (0, start))
        g_score = {start: 0}
        came_from = {}

        while open_set:
            _, current = heapq.heappop(open_set)
            explored_count += 1

            if current == goal:
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.append(start)
                return path[::-1], explored_count

            for neighbor in self.get_neighbors(current):
                if (self.cells[neighbor]["obstacle"] or
                        self.cells[neighbor]["active"] or
                        neighbor in self.reserved_cells):
                    continue

                move_cost = 1 if abs(neighbor[0] - current[0]) + abs(neighbor[1] - current[1]) == 1 else math.sqrt(2)
                tentative_g_score = g_score.get(current, float('inf')) + move_cost

                if tentative_g_score < g_score.get(neighbor, float('inf')):
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g_score
                    f_score = tentative_g_score + heuristic(neighbor, goal)
                    heapq.heappush(open_set, (f_score, neighbor))

        return None, explored_count

    def bfs_search_batch(self, start, goal):
        """BFS implementation for batch testing (no visualization)."""
        explored_count = 0

        queue = deque([[start]])
        visited = {start}

        while queue:
            path = queue.popleft()
            current = path[-1]
            explored_count += 1

            if current == goal:
                return path, explored_count

            for neighbor in self.get_neighbors(current):
                if (neighbor in visited or
                        self.cells[neighbor]["obstacle"] or
                        self.cells[neighbor]["active"] or
                        neighbor in self.reserved_cells):
                    continue

                visited.add(neighbor)
                new_path = list(path)
                new_path.append(neighbor)
                queue.append(new_path)

    def alpha_beta_pathfinding(self, start, goal):
        """
        Enhanced Alpha-Beta pruning algorithm for pathfinding.
        This is an improved version of Minimax with more aggressive pruning.
        """
        start_time = time.time()
        explored_count = 0
        max_depth = 6  # Slightly increased depth compared to Minimax
        max_explored = 600  # Allow more exploration
        timeout = 1.0  # Same timeout as Minimax
        pruned_nodes = 0  # Count pruned nodes for metrics

        # Calculate heuristic distance (Manhattan distance)
        def heuristic(pos):
            return abs(pos[0] - goal[0]) + abs(pos[1] - goal[1])

        # Alpha-Beta function with enhanced pruning
        def alpha_beta(position, depth, alpha, beta, maximizing_player, path):
            nonlocal explored_count, pruned_nodes
            explored_count += 1

            # Early termination if we've explored too many nodes or exceeded timeout
            if explored_count > max_explored or (time.time() - start_time) > timeout:
                return -heuristic(position), path + [position]

            # Mark as visited for visualization (limit visualization to prevent UI freezing)
            if position != start and position != goal and explored_count % 10 == 0:
                self.mark_visited(position)

            # Base cases
            if position == goal:
                return float('inf'), path + [position]

            if depth == 0:
                # Return negative heuristic as score (closer to goal = higher score)
                return -heuristic(position), path + [position]

            # Get valid neighbors
            neighbors = []
            for neighbor in self.get_neighbors(position):
                if (self.cells[neighbor]["obstacle"] or
                    self.cells[neighbor]["active"] or
                    neighbor in self.reserved_cells or
                    neighbor in path):  # Avoid cycles
                    continue
                neighbors.append(neighbor)

            # If no valid moves, return a poor score
            if not neighbors:
                return float('-inf') if maximizing_player else float('inf'), path

            # Enhanced neighbor sorting for better pruning
            if maximizing_player:
                # Sort by heuristic (closest to goal first)
                neighbors.sort(key=lambda n: heuristic(n))
            else:
                # Sort by reverse heuristic (furthest from goal first)
                neighbors.sort(key=lambda n: -heuristic(n))

            if maximizing_player:
                best_score = float('-inf')
                best_path = path

                for neighbor in neighbors:
                    score, new_path = alpha_beta(neighbor, depth - 1, alpha, beta, False, path + [position])

                    if score > best_score:
                        best_score = score
                        best_path = new_path

                    alpha = max(alpha, best_score)
                    if beta <= alpha:
                        # Pruning occurred
                        pruned_nodes += len(neighbors) - neighbors.index(neighbor) - 1
                        break

                return best_score, best_path
            else:
                best_score = float('inf')
                best_path = path

                for neighbor in neighbors:
                    score, new_path = alpha_beta(neighbor, depth - 1, alpha, beta, True, path + [position])

                    if score < best_score:
                        best_score = score
                        best_path = new_path

                    beta = min(beta, best_score)
                    if beta <= alpha:
                        # Pruning occurred
                        pruned_nodes += len(neighbors) - neighbors.index(neighbor) - 1
                        break

                return best_score, best_path

        # Start alpha-beta search with timeout protection
        try:
            _, path = alpha_beta(start, max_depth, float('-inf'), float('inf'), True, [])

            # If search took too long, fall back to A*
            if (time.time() - start_time) > timeout:
                self.update_status("Alpha-Beta timeout - falling back to A*")
                a_star_path, a_star_explored = self.a_star(start, goal)
                explored_count += a_star_explored
                return a_star_path, explored_count
        except Exception as e:
            self.update_status(f"Alpha-Beta error: {str(e)} - falling back to A*")
            a_star_path, a_star_explored = self.a_star(start, goal)
            explored_count += a_star_explored
            return a_star_path, explored_count

        # Update pruned nodes metric
        self.metrics["Alpha-Beta"]["pruned"] += pruned_nodes

        # Clean up the path (remove duplicates and ensure it starts with start)
        if path and path[0] != start:
            path = [start] + path

        # Check if path reaches the goal
        if not path or path[-1] != goal:
            # If goal not reached, try A* as fallback
            self.update_status("Alpha-Beta couldn't reach goal - falling back to A*")
            a_star_path, a_star_explored = self.a_star(start, goal)
            explored_count += a_star_explored
            return a_star_path, explored_count

        return path, explored_count

    def minimax_pathfinding_batch(self, start, goal):
        """
        Minimax algorithm for batch testing (no visualization).
        This is a simplified version of the minimax_pathfinding method.
        """
        start_time = time.time()
        explored_count = 0
        max_depth = 4  # Further reduced depth for batch testing
        max_explored = 300  # Limit the number of nodes to explore
        timeout = 0.5  # Shorter timeout for batch testing

        # Calculate heuristic distance (Manhattan distance)
        def heuristic(pos):
            return abs(pos[0] - goal[0]) + abs(pos[1] - goal[1])

        # Minimax function with alpha-beta pruning
        def minimax(position, depth, alpha, beta, maximizing_player, path):
            nonlocal explored_count
            explored_count += 1

            # Early termination if we've explored too many nodes or exceeded timeout
            if explored_count > max_explored or (time.time() - start_time) > timeout:
                return -heuristic(position), path + [position]

            # Base cases
            if position == goal:
                return float('inf'), path + [position]

            if depth == 0:
                # Return negative heuristic as score (closer to goal = higher score)
                return -heuristic(position), path + [position]

            # Get valid neighbors
            neighbors = []
            for neighbor in self.get_neighbors(position):
                if (self.cells[neighbor]["obstacle"] or
                    self.cells[neighbor]["active"] or
                    neighbor in self.reserved_cells or
                    neighbor in path):  # Avoid cycles
                    continue
                neighbors.append(neighbor)

            # If no valid moves, return a poor score
            if not neighbors:
                return float('-inf') if maximizing_player else float('inf'), path

            if maximizing_player:
                # Sort neighbors by heuristic to improve pruning
                neighbors.sort(key=lambda n: heuristic(n))

                best_score = float('-inf')
                best_path = path

                for neighbor in neighbors:
                    score, new_path = minimax(neighbor, depth - 1, alpha, beta, False, path + [position])

                    if score > best_score:
                        best_score = score
                        best_path = new_path

                    alpha = max(alpha, best_score)
                    if beta <= alpha:
                        break

                return best_score, best_path
            else:
                # Sort neighbors by heuristic (reversed) to improve pruning
                neighbors.sort(key=lambda n: -heuristic(n))

                best_score = float('inf')
                best_path = path

                for neighbor in neighbors:
                    score, new_path = minimax(neighbor, depth - 1, alpha, beta, True, path + [position])

                    if score < best_score:
                        best_score = score
                        best_path = new_path

                    beta = min(beta, best_score)
                    if beta <= alpha:
                        break

                return best_score, best_path

        # Start minimax search with timeout protection
        try:
            _, path = minimax(start, max_depth, float('-inf'), float('inf'), True, [])

            # If search took too long, fall back to A*
            if (time.time() - start_time) > timeout:
                a_star_path, a_star_explored = self.a_star_batch(start, goal)
                explored_count += a_star_explored
                return a_star_path, explored_count
        except Exception:
            a_star_path, a_star_explored = self.a_star_batch(start, goal)
            explored_count += a_star_explored
            return a_star_path, explored_count

        # Clean up the path (remove duplicates and ensure it starts with start)
        if path and path[0] != start:
            path = [start] + path

        # Check if path reaches the goal
        if not path or path[-1] != goal:
            # If goal not reached, try A* as fallback
            a_star_path, a_star_explored = self.a_star_batch(start, goal)
            explored_count += a_star_explored
            return a_star_path, explored_count

        return path, explored_count

    def alpha_beta_pathfinding_batch(self, start, goal):
        """
        Enhanced Alpha-Beta pruning algorithm for batch testing (no visualization).
        This is a simplified version of the alpha_beta_pathfinding method.
        """
        start_time = time.time()
        explored_count = 0
        max_depth = 5  # Depth for batch testing
        max_explored = 400  # Limit the number of nodes to explore
        timeout = 0.5  # Shorter timeout for batch testing
        pruned_nodes = 0  # Count pruned nodes for metrics

        # Calculate heuristic distance (Manhattan distance)
        def heuristic(pos):
            return abs(pos[0] - goal[0]) + abs(pos[1] - goal[1])

        # Alpha-Beta function with enhanced pruning
        def alpha_beta(position, depth, alpha, beta, maximizing_player, path):
            nonlocal explored_count, pruned_nodes
            explored_count += 1

            # Early termination if we've explored too many nodes or exceeded timeout
            if explored_count > max_explored or (time.time() - start_time) > timeout:
                return -heuristic(position), path + [position]

            # Base cases
            if position == goal:
                return float('inf'), path + [position]

            if depth == 0:
                # Return negative heuristic as score (closer to goal = higher score)
                return -heuristic(position), path + [position]

            # Get valid neighbors
            neighbors = []
            for neighbor in self.get_neighbors(position):
                if (self.cells[neighbor]["obstacle"] or
                    self.cells[neighbor]["active"] or
                    neighbor in self.reserved_cells or
                    neighbor in path):  # Avoid cycles
                    continue
                neighbors.append(neighbor)

            # If no valid moves, return a poor score
            if not neighbors:
                return float('-inf') if maximizing_player else float('inf'), path

            # Enhanced neighbor sorting for better pruning
            if maximizing_player:
                # Sort by heuristic (closest to goal first)
                neighbors.sort(key=lambda n: heuristic(n))
            else:
                # Sort by reverse heuristic (furthest from goal first)
                neighbors.sort(key=lambda n: -heuristic(n))

            if maximizing_player:
                best_score = float('-inf')
                best_path = path

                for neighbor in neighbors:
                    score, new_path = alpha_beta(neighbor, depth - 1, alpha, beta, False, path + [position])

                    if score > best_score:
                        best_score = score
                        best_path = new_path

                    alpha = max(alpha, best_score)
                    if beta <= alpha:
                        # Pruning occurred
                        pruned_nodes += len(neighbors) - neighbors.index(neighbor) - 1
                        break

                return best_score, best_path
            else:
                best_score = float('inf')
                best_path = path

                for neighbor in neighbors:
                    score, new_path = alpha_beta(neighbor, depth - 1, alpha, beta, True, path + [position])

                    if score < best_score:
                        best_score = score
                        best_path = new_path

                    beta = min(beta, best_score)
                    if beta <= alpha:
                        # Pruning occurred
                        pruned_nodes += len(neighbors) - neighbors.index(neighbor) - 1
                        break

                return best_score, best_path

        # Start alpha-beta search with timeout protection
        try:
            _, path = alpha_beta(start, max_depth, float('-inf'), float('inf'), True, [])

            # If search took too long, fall back to A*
            if (time.time() - start_time) > timeout:
                a_star_path, a_star_explored = self.a_star_batch(start, goal)
                explored_count += a_star_explored
                return a_star_path, explored_count
        except Exception:
            a_star_path, a_star_explored = self.a_star_batch(start, goal)
            explored_count += a_star_explored
            return a_star_path, explored_count

        # Update pruned nodes metric
        self.metrics["Alpha-Beta"]["pruned"] += pruned_nodes

        # Clean up the path (remove duplicates and ensure it starts with start)
        if path and path[0] != start:
            path = [start] + path

        # Check if path reaches the goal
        if not path or path[-1] != goal:
            # If goal not reached, try A* as fallback
            a_star_path, a_star_explored = self.a_star_batch(start, goal)
            explored_count += a_star_explored
            return a_star_path, explored_count

        return path, explored_count

    def expectimax_pathfinding(self, start, goal):
        """
        Expectimax algorithm adapted for pathfinding.

        In this adaptation:
        - The agent tries to maximize its position (closer to goal)
        - Chance nodes represent uncertainty in the environment
        - We use a depth limit to prevent excessive exploration
        - We return the best path found within the depth limit
        """
        start_time = time.time()
        explored_count = 0
        max_depth = 5  # Limit search depth
        max_explored = 500  # Limit the number of nodes to explore
        timeout = 1.0  # Timeout in seconds
        chance_nodes = 0  # Count chance nodes for metrics

        # Calculate heuristic distance (Manhattan distance)
        def heuristic(pos):
            return abs(pos[0] - goal[0]) + abs(pos[1] - goal[1])

        # Expectimax function
        def expectimax(position, depth, is_max_node, path):
            nonlocal explored_count, chance_nodes
            explored_count += 1

            # Early termination if we've explored too many nodes or exceeded timeout
            if explored_count > max_explored or (time.time() - start_time) > timeout:
                return -heuristic(position), path + [position]

            # Mark as visited for visualization (limit visualization to prevent UI freezing)
            if position != start and position != goal and explored_count % 10 == 0:
                self.mark_visited(position)

            # Base cases
            if position == goal:
                return float('inf'), path + [position]

            if depth == 0:
                # Return negative heuristic as score (closer to goal = higher score)
                return -heuristic(position), path + [position]

            # Get valid neighbors
            neighbors = []
            for neighbor in self.get_neighbors(position):
                if (self.cells[neighbor]["obstacle"] or
                    self.cells[neighbor]["active"] or
                    neighbor in self.reserved_cells or
                    neighbor in path):  # Avoid cycles
                    continue
                neighbors.append(neighbor)

            # If no valid moves, return a poor score
            if not neighbors:
                return float('-inf'), path

            if is_max_node:
                # Max node (agent's turn)
                best_score = float('-inf')
                best_path = path

                # Sort neighbors by heuristic (closest to goal first)
                neighbors.sort(key=lambda n: heuristic(n))

                for neighbor in neighbors:
                    # The next level is a chance node
                    score, new_path = expectimax(neighbor, depth - 1, False, path + [position])

                    if score > best_score:
                        best_score = score
                        best_path = new_path

                return best_score, best_path
            else:
                # Chance node (environment's "turn")
                chance_nodes += 1

                # Calculate expected value across all neighbors
                total_score = 0
                best_path = path
                best_individual_score = float('-inf')

                # Equal probability for each neighbor
                probability = 1.0 / len(neighbors)

                for neighbor in neighbors:
                    score, new_path = expectimax(neighbor, depth - 1, True, path + [position])
                    total_score += score * probability

                    # Keep track of the best individual path for returning
                    if score > best_individual_score:
                        best_individual_score = score
                        best_path = new_path

                # Return expected value and the best path
                return total_score, best_path

        # Start expectimax search with timeout protection
        try:
            _, path = expectimax(start, max_depth, True, [])

            # If search took too long, fall back to A*
            if (time.time() - start_time) > timeout:
                self.update_status("Expectimax timeout - falling back to A*")
                a_star_path, a_star_explored = self.a_star(start, goal)
                explored_count += a_star_explored
                return a_star_path, explored_count
        except Exception as e:
            self.update_status(f"Expectimax error: {str(e)} - falling back to A*")
            a_star_path, a_star_explored = self.a_star(start, goal)
            explored_count += a_star_explored
            return a_star_path, explored_count

        # Update chance nodes metric
        self.metrics["Expectimax"]["chance_nodes"] += chance_nodes

        # Clean up the path (remove duplicates and ensure it starts with start)
        if path and path[0] != start:
            path = [start] + path

        # Check if path reaches the goal
        if not path or path[-1] != goal:
            # If goal not reached, try A* as fallback
            self.update_status("Expectimax couldn't reach goal - falling back to A*")
            a_star_path, a_star_explored = self.a_star(start, goal)
            explored_count += a_star_explored
            return a_star_path, explored_count

        return path, explored_count

    def expectimax_pathfinding_batch(self, start, goal):
        """
        Expectimax algorithm for batch testing (no visualization).
        This is a simplified version of the expectimax_pathfinding method.
        """
        start_time = time.time()
        explored_count = 0
        max_depth = 4  # Reduced depth for batch testing
        max_explored = 300  # Limit the number of nodes to explore
        timeout = 0.5  # Shorter timeout for batch testing
        chance_nodes = 0  # Count chance nodes for metrics

        # Calculate heuristic distance (Manhattan distance)
        def heuristic(pos):
            return abs(pos[0] - goal[0]) + abs(pos[1] - goal[1])

        # Expectimax function
        def expectimax(position, depth, is_max_node, path):
            nonlocal explored_count, chance_nodes
            explored_count += 1

            # Early termination if we've explored too many nodes or exceeded timeout
            if explored_count > max_explored or (time.time() - start_time) > timeout:
                return -heuristic(position), path + [position]

            # Base cases
            if position == goal:
                return float('inf'), path + [position]

            if depth == 0:
                # Return negative heuristic as score (closer to goal = higher score)
                return -heuristic(position), path + [position]

            # Get valid neighbors
            neighbors = []
            for neighbor in self.get_neighbors(position):
                if (self.cells[neighbor]["obstacle"] or
                    self.cells[neighbor]["active"] or
                    neighbor in self.reserved_cells or
                    neighbor in path):  # Avoid cycles
                    continue
                neighbors.append(neighbor)

            # If no valid moves, return a poor score
            if not neighbors:
                return float('-inf'), path

            if is_max_node:
                # Max node (agent's turn)
                best_score = float('-inf')
                best_path = path

                for neighbor in neighbors:
                    # The next level is a chance node
                    score, new_path = expectimax(neighbor, depth - 1, False, path + [position])

                    if score > best_score:
                        best_score = score
                        best_path = new_path

                return best_score, best_path
            else:
                # Chance node (environment's "turn")
                chance_nodes += 1

                # Calculate expected value across all neighbors
                total_score = 0
                best_path = path
                best_individual_score = float('-inf')

                # Equal probability for each neighbor
                probability = 1.0 / len(neighbors)

                for neighbor in neighbors:
                    score, new_path = expectimax(neighbor, depth - 1, True, path + [position])
                    total_score += score * probability

                    # Keep track of the best individual path for returning
                    if score > best_individual_score:
                        best_individual_score = score
                        best_path = new_path

                # Return expected value and the best path
                return total_score, best_path

        # Start expectimax search with timeout protection
        try:
            _, path = expectimax(start, max_depth, True, [])

            # If search took too long, fall back to A*
            if (time.time() - start_time) > timeout:
                a_star_path, a_star_explored = self.a_star_batch(start, goal)
                explored_count += a_star_explored
                return a_star_path, explored_count
        except Exception:
            a_star_path, a_star_explored = self.a_star_batch(start, goal)
            explored_count += a_star_explored
            return a_star_path, explored_count

        # Update chance nodes metric
        self.metrics["Expectimax"]["chance_nodes"] += chance_nodes

        # Clean up the path (remove duplicates and ensure it starts with start)
        if path and path[0] != start:
            path = [start] + path

        # Check if path reaches the goal
        if not path or path[-1] != goal:
            # If goal not reached, try A* as fallback
            a_star_path, a_star_explored = self.a_star_batch(start, goal)
            explored_count += a_star_explored
            return a_star_path, explored_count

        return path, explored_count

    def dfs_search_batch(self, start, goal):
        """DFS implementation for batch testing (no visualization)."""
        explored_count = 0

        stack = [[start]]
        visited = {start}

        while stack:
            path = stack.pop()
            current = path[-1]
            explored_count += 1

            if current == goal:
                return path, explored_count

            neighbors = list(self.get_neighbors(current))
            neighbors.reverse()

            for neighbor in neighbors:
                if (neighbor in visited or
                        self.cells[neighbor]["obstacle"] or
                        self.cells[neighbor]["active"] or
                        neighbor in self.reserved_cells):
                    continue

                visited.add(neighbor)
                new_path = list(path)
                new_path.append(neighbor)
                stack.append(new_path)

        return None, explored_count

    def generate_comparison_report(self, results):
        """Generate a comprehensive comparison report for all algorithms."""
        self.metrics_text.config(state=tk.NORMAL)
        self.metrics_text.delete(1.0, tk.END)

        self.metrics_text.insert(tk.END, "=== ALGORITHM COMPARISON ===\n\n")

        for algo, data in results.items():
            success_text = "SUCCESS" if data["success"] else "PARTIAL"
            self.metrics_text.insert(tk.END, f"{algo}: {success_text}\n")
            self.metrics_text.insert(tk.END, f"Total Time: {data['time']:.4f} seconds\n")

            if "stats" in data:
                stats = data["stats"]
                self.metrics_text.insert(tk.END, f"Moves: {stats['moves']}\n")
                if stats['moves'] > 0:
                    self.metrics_text.insert(tk.END, f"Avg Path Length: {stats['path_length'] / stats['moves']:.2f}\n")
                    self.metrics_text.insert(tk.END, f"Avg Cells Explored: {stats['explored'] / stats['moves']:.2f}\n")

                # Add success rate to the report
                if 'success_rate' in stats:
                    self.metrics_text.insert(tk.END, f"Success Rate: {stats['success_rate']:.1f}%\n")

            self.metrics_text.insert(tk.END, "\n")

        # Summary comparison
        self.metrics_text.insert(tk.END, "=== SUMMARY ===\n")

        # Sort by success rate first, then by time
        sorted_algos = sorted(results.keys(),
                              key=lambda a: (-results[a]["stats"].get("success_rate", 0), results[a]["time"]))

        self.metrics_text.insert(tk.END, "Ranking by performance:\n")
        for i, algo in enumerate(sorted_algos):
            success_rate = results[algo]["stats"].get("success_rate", 0)
            total_time = results[algo]["time"]
            self.metrics_text.insert(tk.END, f"{i + 1}. {algo} ({success_rate:.1f}%) (Time: {total_time:.4f}s)\n")

        self.metrics_text.config(state=tk.DISABLED)

    # Set speed for animation (can be adjusted in UI)
    @property
    def movement_speed(self):
        """Get the current movement speed."""
        return self.speed_var.get()

    @movement_speed.setter
    def movement_speed(self, value):
        """Set the movement speed."""
        self.speed_var.set(value)


# Run the application
if __name__ == "__main__":
    root = tk.Tk()
    app = InteractiveGrid(root)
    root.mainloop()

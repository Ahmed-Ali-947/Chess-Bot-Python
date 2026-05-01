"""
Chess GUI using Tkinter - Visual interface for the chess game
Run: python chess_gui.py
"""

import tkinter as tk
from tkinter import ttk, messagebox
import chess
import sys
from datetime import datetime
from Chessbot import ChessAI, SEARCH_DEPTH, PIECE_VALUES, PIECE_SQUARE_TABLES

class ChessGUI:
    """Main GUI application for chess game"""
    
    # Colors
    LIGHT_SQUARE = "#F0D9B5"
    DARK_SQUARE = "#B58863"
    HIGHLIGHT_COLOR = "#FFFF00"
    LAST_MOVE_COLOR = "#CDEBC4"
    CHECK_COLOR = "#FF4444"
    LEGAL_MOVE_COLOR = "#90EE90"
    
    # Piece to unicode mapping
    PIECE_SYMBOLS = {
        'K': '♔', 'Q': '♕', 'R': '♖', 'B': '♗', 'N': '♘', 'P': '♙',
        'k': '♚', 'q': '♛', 'r': '♜', 'b': '♝', 'n': '♞', 'p': '♟'
    }
    
    def __init__(self, root):
        self.root = root
        self.root.title("Chess Game - You play White, AI plays Black")
        self.root.geometry("1000x700")
        self.root.resizable(True, True)
        
        # Game state
        self.board = chess.Board()
        self.ai = ChessAI(depth=SEARCH_DEPTH)
        self.selected_square = None
        self.legal_moves_for_selected = []
        self.game_over = False
        self.last_move = None
        self.flipped = False
        self.ai_mode = False
        
        # Move tracking
        self.move_history = []
        
        # Setup GUI
        self.setup_menu()
        self.setup_toolbar()
        self.setup_main_frame()
        self.setup_status_bar()
        
        # Bind keyboard shortcuts
        self.root.bind('<Control-z>', self.undo_move)
        self.root.bind('<Control-n>', self.new_game)
        self.root.bind('<F1>', self.show_help)
        
        # Initial board display
        self.refresh_board()
        self.update_status()
        
    def setup_menu(self):
        """Create menu bar"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # Game menu
        game_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Game", menu=game_menu)
        game_menu.add_command(label="New Game", command=self.new_game, accelerator="Ctrl+N")
        game_menu.add_command(label="Undo Move", command=self.undo_move, accelerator="Ctrl+Z")
        game_menu.add_separator()
        game_menu.add_command(label="Flip Board", command=self.flip_board)
        game_menu.add_separator()
        game_menu.add_command(label="Exit", command=self.root.quit, accelerator="Ctrl+Q")
        
        # AI menu
        ai_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="AI", menu=ai_menu)
        ai_menu.add_command(label="AI Makes Move", command=self.ai_move)
        ai_menu.add_separator()
        
        # Difficulty submenu
        self.difficulty_var = tk.IntVar(value=SEARCH_DEPTH)
        difficulty_menu = tk.Menu(ai_menu, tearoff=0)
        ai_menu.add_cascade(label="Difficulty", menu=difficulty_menu)
        difficulty_menu.add_radiobutton(label="Easy (Depth 2)", variable=self.difficulty_var, 
                                       value=2, command=self.change_difficulty)
        difficulty_menu.add_radiobutton(label="Medium (Depth 3)", variable=self.difficulty_var, 
                                       value=3, command=self.change_difficulty)
        difficulty_menu.add_radiobutton(label="Hard (Depth 4)", variable=self.difficulty_var, 
                                       value=4, command=self.change_difficulty)
        difficulty_menu.add_radiobutton(label="Expert (Depth 5)", variable=self.difficulty_var, 
                                       value=5, command=self.change_difficulty)
        
        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Show Legal Moves", command=self.show_legal_moves)
        view_menu.add_command(label="Show Evaluation", command=self.show_evaluation)
        view_menu.add_separator()
        self.show_coords_var = tk.BooleanVar(value=True)
        view_menu.add_checkbutton(label="Show Coordinates", variable=self.show_coords_var, 
                                 command=self.refresh_board)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="Rules", command=self.show_rules)
        help_menu.add_command(label="About", command=self.show_about)
        
    def setup_toolbar(self):
        """Create toolbar with buttons"""
        toolbar = tk.Frame(self.root, bd=1, relief=tk.RAISED)
        toolbar.pack(side=tk.TOP, fill=tk.X)
        
        # Buttons
        tk.Button(toolbar, text="New Game", command=self.new_game, 
                 relief=tk.FLAT, padx=10).pack(side=tk.LEFT, padx=2, pady=2)
        tk.Button(toolbar, text="Undo Move", command=self.undo_move, 
                 relief=tk.FLAT, padx=10).pack(side=tk.LEFT, padx=2, pady=2)
        tk.Button(toolbar, text="AI Move", command=self.ai_move, 
                 relief=tk.FLAT, padx=10).pack(side=tk.LEFT, padx=2, pady=2)
        tk.Button(toolbar, text="Flip Board", command=self.flip_board, 
                 relief=tk.FLAT, padx=10).pack(side=tk.LEFT, padx=2, pady=2)
        
        # Difficulty label
        tk.Label(toolbar, text="Difficulty:").pack(side=tk.LEFT, padx=(20, 5))
        self.difficulty_label = tk.Label(toolbar, text="Medium", fg="blue")
        self.difficulty_label.pack(side=tk.LEFT)
        
    def setup_main_frame(self):
        """Create main game frame with board and info panel"""
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Board frame (left side)
        self.board_frame = tk.Frame(self.main_frame, width=600, height=600)
        self.board_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.board_frame.pack_propagate(False)
        
        # Create canvas for chess board
        self.canvas = tk.Canvas(self.board_frame, width=600, height=600, bg="white")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Bind click event
        self.canvas.bind("<Button-1>", self.on_square_clicked)
        
        # Info panel (right side)
        self.info_frame = tk.Frame(self.main_frame, width=300, bg="#f0f0f0")
        self.info_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(10, 0))
        self.info_frame.pack_propagate(False)
        
        # Game info
        tk.Label(self.info_frame, text="Game Information", font=("Arial", 14, "bold"), 
                bg="#f0f0f0").pack(pady=10)
        
        # Turn indicator
        self.turn_label = tk.Label(self.info_frame, text="", font=("Arial", 12), 
                                  bg="#f0f0f0", pady=10)
        self.turn_label.pack()
        
        # Check indicator
        self.check_label = tk.Label(self.info_frame, text="", font=("Arial", 12, "bold"), 
                                   fg="red", bg="#f0f0f0")
        self.check_label.pack()
        
        # Move history
        tk.Label(self.info_frame, text="Move History", font=("Arial", 12, "bold"), 
                bg="#f0f0f0").pack(pady=(20, 5))
        
        # Create frame for history with scrollbar
        history_frame = tk.Frame(self.info_frame)
        history_frame.pack(pady=5, fill=tk.BOTH, expand=True)
        
        self.history_text = tk.Text(history_frame, height=15, width=30, 
                                   font=("Courier", 10))
        self.history_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Scrollbar for history
        scrollbar = tk.Scrollbar(history_frame, command=self.history_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.history_text.config(yscrollcommand=scrollbar.set)
        
        # Evaluation display
        tk.Label(self.info_frame, text="Position Evaluation", font=("Arial", 10, "bold"), 
                bg="#f0f0f0").pack(pady=(10, 5))
        
        self.eval_label = tk.Label(self.info_frame, text="", font=("Arial", 12), 
                                   bg="#f0f0f0", pady=5)
        self.eval_label.pack()
        
    def setup_status_bar(self):
        """Create status bar at bottom"""
        self.status_bar = tk.Label(self.root, text="Ready", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
    def refresh_board(self):
        """Draw the chess board on canvas"""
        self.canvas.delete("all")
        square_size = 600 // 8
        
        # Draw squares
        for row in range(8):
            for col in range(8):
                x1 = col * square_size
                y1 = row * square_size
                x2 = x1 + square_size
                y2 = y1 + square_size
                
                # Determine square color
                is_light = (row + col) % 2 == 0
                
                # Check if this square is selected
                current_square = row * 8 + col
                if self.flipped:
                    current_square = chess.square_mirror(current_square)
                
                if self.selected_square == current_square:
                    color = self.HIGHLIGHT_COLOR
                elif self.last_move and (self.last_move.from_square == current_square or 
                                        self.last_move.to_square == current_square):
                    color = self.LAST_MOVE_COLOR
                elif self.board.is_check() and self.board.king(self.board.turn) == current_square:
                    color = self.CHECK_COLOR
                else:
                    color = self.LIGHT_SQUARE if is_light else self.DARK_SQUARE
                    
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="")
                
                # Show coordinates
                if self.show_coords_var.get():
                    if col == 0:  # Rank numbers
                        rank_num = 8 - row if not self.flipped else row + 1
                        self.canvas.create_text(x1 + 5, y1 + 5, anchor=tk.NW, 
                                               text=str(rank_num), font=("Arial", 8))
                    if row == 7:  # File letters
                        file_letter = chr(97 + col) if not self.flipped else chr(104 - col)
                        self.canvas.create_text(x2 - 5, y2 - 5, anchor=tk.SE, 
                                               text=file_letter, font=("Arial", 8))
        
        # Draw pieces
        for row in range(8):
            for col in range(8):
                square = row * 8 + col
                if self.flipped:
                    square = chess.square_mirror(square)
                    
                piece = self.board.piece_at(square)
                if piece:
                    x = col * square_size + square_size // 2
                    y = row * square_size + square_size // 2
                    
                    # Get piece symbol
                    symbol = piece.symbol()
                    piece_text = self.PIECE_SYMBOLS.get(symbol, symbol)
                    
                    # Draw piece
                    # Draw outline first (slightly offset)
                    if piece.color == chess.WHITE:
                        # Draw outline (only for white pieces)
                        for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
                            self.canvas.create_text(
                                x+dx, y+dy,
                                text=piece_text,
                                font=("Arial", 36, "bold"),
                                fill="black"
                            )
                        
                        # Draw white piece
                        self.canvas.create_text(
                            x, y,
                            text=piece_text,
                            font=("Arial", 36, "bold"),
                            fill="#FFFFFF"
                        )
                    else:
                        # Draw black piece normally (no outline)
                        self.canvas.create_text(
                            x, y,
                            text=piece_text,
                            font=("Arial", 36, "bold"),
                            fill="#000000"
                        )
        
        # Draw legal move indicators
        if self.selected_square is not None and self.legal_moves_for_selected:
            for move in self.legal_moves_for_selected:
                to_square = move.to_square
                if self.flipped:
                    to_square = chess.square_mirror(to_square)
                    
                to_row = to_square // 8
                to_col = to_square % 8
                x = to_col * square_size + square_size // 2
                y = to_row * square_size + square_size // 2
                r = square_size // 6
                self.canvas.create_oval(x - r, y - r, x + r, y + r, 
                                       fill=self.LEGAL_MOVE_COLOR, outline="black", width=2)
        
    def on_square_clicked(self, event):
        """Handle square click events"""
        if self.game_over:
            messagebox.showinfo("Game Over", "Game is over! Start a new game.")
            return
        
        # Get clicked square
        square_size = 600 // 8
        col = event.x // square_size
        row = event.y // square_size
        
        if 0 <= row < 8 and 0 <= col < 8:
            square = row * 8 + col
            if self.flipped:
                square = chess.square_mirror(square)
            
            if self.selected_square is not None:
                # Try to make a move
                move = chess.Move(self.selected_square, square)
                
                # Check for promotion
                piece = self.board.piece_at(self.selected_square)
                if piece and piece.piece_type == chess.PAWN:
                    target_rank = square // 8
                    if (piece.color == chess.WHITE and target_rank == 7) or \
                       (piece.color == chess.BLACK and target_rank == 0):
                        # Show promotion dialog
                        promotion = self.show_promotion_dialog()
                        if promotion:
                            move = chess.Move(self.selected_square, square, promotion=promotion)
                
                if move in self.board.legal_moves:
                    self.make_move(move)
                else:
                    # Invalid move, clear selection
                    self.status_bar.config(text="Invalid move!")
                
                # Clear selection
                self.selected_square = None
                self.legal_moves_for_selected = []
            else:
                # Select piece if it's the current player's piece
                piece = self.board.piece_at(square)
                if piece and piece.color == self.board.turn:
                    self.selected_square = square
                    self.legal_moves_for_selected = [m for m in self.board.legal_moves 
                                                     if m.from_square == square]
                    piece_name = chess.piece_name(piece.piece_type).capitalize()
                    self.status_bar.config(text=f"Selected {piece_name}")
                else:
                    if piece:
                        self.status_bar.config(text="Not your piece!")
                    else:
                        self.status_bar.config(text="No piece there!")
            
            self.refresh_board()
            self.update_status()
    
    def make_move(self, move):
        """Execute a move and update GUI"""
        # Store move for potential undo
        self.last_move = move
        
        # Get move in SAN format for display
        move_san = self.board.san(move)
        
        # Make the move
        self.board.push(move)
        
        # Update move history
        move_number = len(self.move_history) // 2 + 1
        if self.board.turn == chess.BLACK:  # White just moved
            self.move_history.append(f"{move_number}. {move_san}")
        else:  # Black just moved
            if self.move_history:
                self.move_history[-1] += f" {move_san}"
            else:
                self.move_history.append(f"{move_number}. ... {move_san}")
        
        self.update_move_history()
        
        # Update status
        self.status_bar.config(text=f"Move played: {move_san}")
        
        # Refresh display
        self.refresh_board()
        self.update_status()
        
        # Check if game over
        if self.board.is_game_over():
            self.handle_game_over()
            return
        
        # AI move if it's AI's turn
        if self.board.turn == chess.BLACK:
            self.root.after(500, self.ai_move)  # Delay for better UX
    
    def ai_move(self):
        """AI makes a move"""
        if self.game_over:
            return
        
        if self.board.turn == chess.BLACK:
            self.status_bar.config(text="AI is thinking...")
            self.root.update()
            
            # Get AI move
            move = self.ai.find_best_move(self.board)
            
            if move:
                move_san = self.board.san(move)
                self.board.push(move)
                
                # Update move history
                move_number = len(self.move_history) // 2 + 1
                if self.move_history and not self.move_history[-1].startswith(str(move_number)):
                    self.move_history[-1] += f" {move_san}"
                else:
                    self.move_history.append(f"{move_number}. ... {move_san}")
                
                self.update_move_history()
                
                self.status_bar.config(text=f"AI played: {move_san}")
                self.refresh_board()
                self.update_status()
                
                if self.board.is_game_over():
                    self.handle_game_over()
            else:
                self.status_bar.config(text="AI has no legal moves!")
                self.handle_game_over()
    
    def update_move_history(self):
        """Update the move history display"""
        self.history_text.delete(1.0, tk.END)
        for move in self.move_history:
            self.history_text.insert(tk.END, f"{move}\n")
        self.history_text.see(tk.END)
    
    def update_status(self):
        """Update status displays (turn, check, evaluation)"""
        # Update turn indicator
        if not self.board.is_game_over():
            if self.board.turn == chess.WHITE:
                turn_text = "White's turn (You)"
                turn_color = "black"
            else:
                turn_text = "Black's turn (AI)"
                turn_color = "red"
            self.turn_label.config(text=turn_text, fg=turn_color)
        
        # Check indicator
        if self.board.is_check():
            self.check_label.config(text="⚠️ CHECK! ⚠️")
        else:
            self.check_label.config(text="")
        
        # Update evaluation
        eval_score = self.ai.evaluate(self.board)
        eval_value = eval_score / 100.0
        if eval_value > 0:
            eval_text = f"White is winning by {eval_value:.2f}"
        elif eval_value < 0:
            eval_text = f"Black is winning by {-eval_value:.2f}"
        else:
            eval_text = "Position is equal"
        self.eval_label.config(text=eval_text)
        
        # Update difficulty label
        difficulty_text = {2: "Easy", 3: "Medium", 4: "Hard", 5: "Expert"}
        self.difficulty_label.config(text=difficulty_text.get(self.difficulty_var.get(), "Medium"))
    
    def show_promotion_dialog(self):
        """Show promotion piece selection dialog"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Promotion")
        dialog.geometry("300x150")
        dialog.transient(self.root)
        dialog.grab_set()
        
        tk.Label(dialog, text="Promote pawn to:", font=("Arial", 12)).pack(pady=10)
        
        promotion_var = tk.StringVar(value="q")
        frame = tk.Frame(dialog)
        frame.pack(pady=10)
        
        pieces = [("Queen", "q", "♕"), ("Rook", "r", "♖"), 
                 ("Bishop", "b", "♗"), ("Knight", "n", "♘")]
        
        for piece, value, symbol in pieces:
            tk.Radiobutton(frame, text=f"{piece} {symbol}", variable=promotion_var, 
                          value=value).pack(side=tk.LEFT, padx=5)
        
        result = None
        
        def on_confirm():
            nonlocal result
            result = promotion_var.get()
            dialog.destroy()
        
        tk.Button(dialog, text="Confirm", command=on_confirm, width=10).pack(pady=10)
        
        self.root.wait_window(dialog)
        
        promotion_map = {'q': chess.QUEEN, 'r': chess.ROOK, 'b': chess.BISHOP, 'n': chess.KNIGHT}
        return promotion_map.get(result)
    
    def handle_game_over(self):
        """Handle game over state"""
        self.game_over = True
        
        if self.board.is_checkmate():
            winner = "Black (AI)" if self.board.turn == chess.WHITE else "White (You)"
            messagebox.showinfo("Game Over", f"Checkmate! {winner} wins!")
        elif self.board.is_stalemate():
            messagebox.showinfo("Game Over", "Stalemate! It's a draw.")
        elif self.board.is_insufficient_material():
            messagebox.showinfo("Game Over", "Draw due to insufficient material.")
        else:
            messagebox.showinfo("Game Over", "Game Over!")
        
        self.status_bar.config(text="Game Over. Start a new game (Ctrl+N)")
    
    def new_game(self, event=None):
        """Start a new game"""
        self.board = chess.Board()
        self.selected_square = None
        self.legal_moves_for_selected = []
        self.move_history = []
        self.game_over = False
        self.last_move = None
        
        self.update_move_history()
        self.refresh_board()
        self.update_status()
        self.status_bar.config(text="New game started! White moves first.")
    
    def undo_move(self, event=None):
        """Undo the last move(s)"""
        if self.game_over:
            return
        
        try:
            # Undo last move
            self.board.pop()
            if self.move_history:
                self.move_history.pop()
            
            # If it was AI's turn, undo one more to go back to player's turn
            if self.board.turn == chess.BLACK and self.move_history:
                self.board.pop()
                if self.move_history:
                    self.move_history.pop()
            
            self.selected_square = None
            self.legal_moves_for_selected = []
            self.game_over = False
            self.last_move = None
            
            self.update_move_history()
            self.refresh_board()
            self.update_status()
            self.status_bar.config(text="Undo successful")
        except IndexError:
            self.status_bar.config(text="No moves to undo")
    
    def flip_board(self):
        """Flip the board view"""
        self.flipped = not self.flipped
        self.selected_square = None
        self.legal_moves_for_selected = []
        self.refresh_board()
    
    def change_difficulty(self):
        """Change AI difficulty"""
        depth = self.difficulty_var.get()
        self.ai.depth = depth
        self.status_bar.config(text=f"Difficulty changed to depth {depth}")
    
    def show_legal_moves(self):
        """Show all legal moves in a dialog"""
        moves = list(self.board.legal_moves)
        moves_text = "\n".join([f"{i+1}. {self.board.san(m)}" for i, m in enumerate(moves[:50])])
        if len(moves) > 50:
            moves_text += f"\n\n... and {len(moves) - 50} more moves"
        
        messagebox.showinfo("Legal Moves", f"Legal moves ({len(moves)}):\n\n{moves_text}")
    
    def show_evaluation(self):
        """Show detailed position evaluation"""
        eval_score = self.ai.evaluate(self.board)
        detail = f"""
Position Evaluation: {eval_score/100:.2f}

Material Balance:
White: {self.get_material_balance(chess.WHITE):.2f}
Black: {self.get_material_balance(chess.BLACK):.2f}

Overall: {'White' if eval_score > 0 else 'Black' if eval_score < 0 else 'Equal'} is winning
"""
        messagebox.showinfo("Position Evaluation", detail)
    
    def get_material_balance(self, color):
        """Calculate material balance for a color"""
        total = 0
        for square in chess.SQUARES:
            piece = self.board.piece_at(square)
            if piece and piece.color == color:
                total += PIECE_VALUES.get(piece.piece_type, 0)
        return total / 100
    
    def show_rules(self):
        """Show chess rules"""
        rules = """CHESS RULES

Basic Moves:
• Pawn: Forward 1 or 2 squares (first move), capture diagonally
• Knight: L-shape (2 squares in one direction, 1 perpendicular)
• Bishop: Diagonally any number of squares
• Rook: Horizontally or vertically any number of squares
• Queen: Any direction any number of squares
• King: 1 square in any direction

Special Moves:
• Castling: Move king 2 squares toward rook, rook jumps to other side
• En Passant: Capture pawn that just moved 2 squares as if it moved 1
• Promotion: Pawn becomes Queen, Rook, Bishop, or Knight on last rank

Game Endings:
• Checkmate: King is under attack and cannot escape
• Stalemate: No legal moves but king not in check (draw)
• Draw: By agreement, repetition, or 50-move rule"""
        
        messagebox.showinfo("Chess Rules", rules)
    
    def show_about(self):
        """Show about dialog"""
        about = """Chess Game with GUI
Version 1.0

A complete chess game with AI opponent using minimax algorithm.

Features:
• Graphical board with piece movement
• AI opponent with adjustable difficulty
• Move history and position evaluation
• Undo moves and board flipping
• Unicode chess pieces

Created with Python, Tkinter, and python-chess"""
        
        messagebox.showinfo("About", about)
    
    def show_help(self, event=None):
        """Show help dialog"""
        help_text = """HOW TO PLAY

Moving Pieces:
1. Click on a piece to select it (highlighted in yellow)
2. Click on a highlighted square to move there
3. Green circles show legal moves

Keyboard Shortcuts:
• Ctrl+N - New game
• Ctrl+Z - Undo last move
• F1 - Show this help

Game Controls:
• Use toolbar buttons for quick actions
• Flip board to see from Black's perspective
• Check evaluation to see who's winning

AI Settings:
• Adjust difficulty from AI menu
• Higher depth = stronger but slower AI
• Click "AI Move" to force AI to play"""
        
        messagebox.showinfo("Help", help_text)


def main():
    root = tk.Tk()
    app = ChessGUI(root)
    
    # Center window on screen
    root.update_idletasks()
    width = 1000
    height = 700
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')
    
    root.mainloop()


if __name__ == "__main__":
    main()
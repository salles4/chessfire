import tkinter as tk
import chess

class ChessGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Python Action Chess")
        self.root.resizable(False, False)
        
        self.board = chess.Board()
        self.buttons = {}
        self.selected_square = None

        # Map python-chess internal pieces to Unicode characters
        self.unicode_pieces = {
            'r': '♜', 'n': '♞', 'b': '♝', 'q': '♛', 'k': '♚', 'p': '♟',
            'R': '♖', 'N': '♘', 'B': '♗', 'Q': '♕', 'K': '♔', 'P': '♙',
            None: ''
        }

        self.create_board()
        self.update_board()

    def create_board(self):
        for row in range(8):
            for col in range(8):
                # Standard chess board colors
                color = "#f0d9b5" if (row + col) % 2 == 0 else "#b58863"
                
                # python-chess uses 0 for A1 and 63 for H8. 
                # This math maps the Tkinter visual grid to the engine's internal grid.
                square_index = (7 - row) * 8 + col 
                
                btn = tk.Button(self.root, text='', font=('Arial', 28), bg=color,
                                activebackground="#ffce9e", relief="flat",
                                command=lambda sq=square_index: self.on_click(sq),
                                height=2, width=4)
                btn.grid(row=row, column=col)
                self.buttons[square_index] = btn

    def on_click(self, square):
        # Step 1: Select a piece
        if self.selected_square is None:
            piece = self.board.piece_at(square)
            # Only allow selecting your own pieces
            if piece and piece.color == self.board.turn:
                self.selected_square = square
                self.buttons[square].config(bg="#ffce9e") # Highlight selected square
        
        # Step 2: Attempt to move
        else:
            move = chess.Move(self.selected_square, square)
            
            # Handle pawn promotion (auto-promote to Queen for simplicity)
            piece = self.board.piece_at(self.selected_square)
            if piece and piece.piece_type == chess.PAWN:
                if chess.square_rank(square) == 0 or chess.square_rank(square) == 7:
                    move = chess.Move(self.selected_square, square, promotion=chess.QUEEN)

            # Execute move if legal
            if move in self.board.legal_moves:
                self.board.push(move)
            
            # Reset selection and refresh UI
            self.selected_square = None
            self.update_board()

    def update_board(self):
        for square, btn in self.buttons.items():
            # Reset background colors
            row = 7 - (square // 8)
            col = square % 8
            color = "#f0d9b5" if (row + col) % 2 == 0 else "#b58863"
            btn.config(bg=color)

            # Update piece symbols
            piece = self.board.piece_at(square)
            symbol = self.unicode_pieces.get(piece.symbol() if piece else None, '')
            
            # Color the unicode characters
            text_color = "black" if piece and piece.color == chess.BLACK else "white"
            btn.config(text=symbol, fg=text_color)

        # Check for game over
        if self.board.is_game_over():
            self.root.title("Game Over!")

if __name__ == "__main__":
    root = tk.Tk()
    gui = ChessGUI(root)
    root.mainloop()
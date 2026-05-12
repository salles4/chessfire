"""
⚔ COMBAT CHESS ⚔
A full chess game with animated combat sequences when pieces capture.
Pieces use weapons (swords, guns, cannons, magic) to defeat opponents.

Requirements:
    pip install chess

Run:
    python combat_chess.py
"""

import tkinter as tk
from tkinter import font as tkfont
import chess
import math
import random
import time
import threading


# ─── Color palette ────────────────────────────────────────────────────────────
BG_DARK       = "#0a0a0f"
BG_MID        = "#12101a"
GOLD          = "#c8953a"
GOLD_LIGHT    = "#e8b85a"
GOLD_DIM      = "#8a6030"
RED_BRIGHT    = "#e84040"
RED_DIM       = "#8a2020"
LIGHT_SQ      = "#d4a96a"
DARK_SQ       = "#7a4e28"
SEL_SQ        = "#e8c840"
LEGAL_DOT     = "#50c850"
WHITE_TEXT    = "#f0ead8"
GRAY_TEXT     = "#8a7a6a"
OVERLAY_BG    = "#0d0918"
ARENA_BG      = "#100a18"

# ─── Piece unicode ─────────────────────────────────────────────────────────────
WHITE_PIECES = {"p":"♙","n":"♘","b":"♗","r":"♖","q":"♕","k":"♔"}
BLACK_PIECES = {"p":"♟","n":"♞","b":"♝","r":"♜","q":"♛","k":"♚"}
PIECE_NAMES  = {"p":"Pawn","n":"Knight","b":"Bishop","r":"Rook","q":"Queen","k":"King"}

# ─── Weapon definitions ────────────────────────────────────────────────────────
WEAPONS = {
    "p": {"name": "Bayonet",    "icon": "🗡",  "color": "#c0c080", "type": "sword"},
    "n": {"name": "Longsword",  "icon": "⚔",  "color": "#e0e0ff", "type": "sword"},
    "b": {"name": "Musket",     "icon": "🔫",  "color": "#c08040", "type": "gun"},
    "r": {"name": "Cannon",     "icon": "💣",  "color": "#ff8020", "type": "cannon"},
    "q": {"name": "Dark Magic", "icon": "✦",   "color": "#c040ff", "type": "magic"},
    "k": {"name": "Royal Blade","icon": "⚔",  "color": "#ffd700", "type": "sword"},
}

FILES = list("abcdefgh")


# ─── Particle system ───────────────────────────────────────────────────────────
class Particle:
    def __init__(self, x, y, vx, vy, color, size, life, grav=0.15):
        self.x = x; self.y = y
        self.vx = vx; self.vy = vy
        self.color = color; self.size = size
        self.life = life; self.max_life = life
        self.grav = grav

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += self.grav
        self.life -= 1
        self.vx *= 0.97

    @property
    def alpha(self):
        return self.life / self.max_life

    @property
    def alive(self):
        return self.life > 0


# ─── Main Application ──────────────────────────────────────────────────────────
class CombatChess:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("⚔  Combat Chess  ⚔")
        self.root.configure(bg=BG_DARK)
        self.root.resizable(False, False)

        self.board = chess.Board()
        self.selected_square = None
        self.legal_targets = set()
        self.animating = False
        self.particles: list[Particle] = []

        self._build_fonts()
        self._build_ui()
        self.render_board()

    # ── Fonts ──────────────────────────────────────────────────────────────────
    def _build_fonts(self):
        self.font_piece   = tkfont.Font(family="Segoe UI Emoji", size=28)
        self.font_piece_sm= tkfont.Font(family="Segoe UI Emoji", size=20)
        self.font_title   = tkfont.Font(family="Georgia", size=20, weight="bold")
        self.font_status  = tkfont.Font(family="Georgia", size=11, slant="italic")
        self.font_coord   = tkfont.Font(family="Georgia", size=8)
        self.font_btn     = tkfont.Font(family="Georgia", size=10, weight="bold")
        self.font_combat  = tkfont.Font(family="Georgia", size=13, weight="bold")
        self.font_big     = tkfont.Font(family="Segoe UI Emoji", size=48)
        self.font_weapon  = tkfont.Font(family="Segoe UI Emoji", size=36)

    # ── UI layout ──────────────────────────────────────────────────────────────
    def _build_ui(self):
        # ── title
        tk.Label(self.root, text="⚔  COMBAT CHESS  ⚔",
                 font=self.font_title, bg=BG_DARK, fg=GOLD).pack(pady=(14,4))

        # ── status
        self.status_var = tk.StringVar(value="White's turn — select a piece")
        tk.Label(self.root, textvariable=self.status_var,
                 font=self.font_status, bg=BG_DARK, fg=GRAY_TEXT, height=1).pack()

        # ── 3-D board frame (outer bevel)
        bevel = tk.Frame(self.root, bg=GOLD_DIM, bd=0)
        bevel.pack(padx=18, pady=10)

        inner = tk.Frame(bevel, bg="#3a2010", bd=0)
        inner.pack(padx=3, pady=3)

        # rank/file label frame
        grid_frame = tk.Frame(inner, bg=BG_MID)
        grid_frame.pack(padx=2, pady=2)

        SQ = 68   # square size px

        # file labels (top)
        for c, f in enumerate(FILES):
            tk.Label(grid_frame, text=f, width=3, font=self.font_coord,
                     bg=BG_MID, fg=GOLD_DIM).grid(row=0, column=c+1, sticky="s", pady=(4,0))

        self.sq_canvas: dict[str, tk.Canvas] = {}
        self.sq_buttons: dict[str, tk.Label] = {}

        for r in range(8):
            visual_row = 7 - r   # row 0 = rank 8 at top
            # rank label
            tk.Label(grid_frame, text=str(r+1), font=self.font_coord,
                     bg=BG_MID, fg=GOLD_DIM, width=2).grid(
                     row=7-r+1, column=0, sticky="e", padx=(4,2))

            for c in range(8):
                sq_name = FILES[c] + str(r+1)
                is_light = (r + c) % 2 != 0
                base_color = LIGHT_SQ if is_light else DARK_SQ

                cv = tk.Canvas(grid_frame, width=SQ, height=SQ,
                               bg=base_color, highlightthickness=0, cursor="hand2")
                cv.grid(row=visual_row+1, column=c+1)
                cv.bind("<Button-1>", lambda e, sq=sq_name: self._on_click(sq))

                self.sq_canvas[sq_name] = cv

        # ── game-over label
        self.gameover_var = tk.StringVar()
        self.gameover_lbl = tk.Label(self.root, textvariable=self.gameover_var,
                                     font=tkfont.Font(family="Georgia",size=16,weight="bold"),
                                     bg=BG_DARK, fg=RED_BRIGHT)
        self.gameover_lbl.pack(pady=(0,4))

        # ── buttons
        btn_frame = tk.Frame(self.root, bg=BG_DARK)
        btn_frame.pack(pady=(0,14))

        self._make_btn(btn_frame, "⟳  New Game", self.new_game).pack(side="left", padx=8)
        self._make_btn(btn_frame, "↩  Undo Move", self.undo_move).pack(side="left", padx=8)

        # ── combat overlay (hidden initially)
        self._build_combat_overlay()

    def _make_btn(self, parent, text, cmd):
        return tk.Button(parent, text=text, command=cmd,
                         font=self.font_btn, bg="#1e1008", fg=GOLD,
                         activebackground="#3a2010", activeforeground=GOLD_LIGHT,
                         relief="flat", bd=0, padx=14, pady=6,
                         highlightthickness=1, highlightbackground=GOLD_DIM,
                         cursor="hand2")

    # ── Combat overlay ─────────────────────────────────────────────────────────
    def _build_combat_overlay(self):
        """Toplevel window that shows the battle animation."""
        self.overlay = tk.Toplevel(self.root)
        self.overlay.withdraw()
        self.overlay.overrideredirect(True)
        self.overlay.configure(bg=OVERLAY_BG)
        self.overlay.attributes("-topmost", True)

        W, H = 480, 300
        self.overlay_w = W; self.overlay_h = H

        # Canvas covers the whole overlay
        self.arena = tk.Canvas(self.overlay, width=W, height=H,
                               bg=ARENA_BG, highlightthickness=2,
                               highlightbackground=GOLD_DIM)
        self.arena.pack()

        # Title
        self.arena.create_text(W//2, 20, text="⚔  BATTLE  ⚔",
                               font=tkfont.Font(family="Georgia",size=14,weight="bold"),
                               fill=GOLD, tags="title")

        # Grid lines (arena floor)
        for i in range(0, W, 40):
            self.arena.create_line(i, 40, i, H, fill="#1e1830", width=1)
        for j in range(40, H, 40):
            self.arena.create_line(0, j, W, j, fill="#1e1830", width=1)

        # Divider
        self.arena.create_line(W//2, 50, W//2, H-60,
                               fill="#3a1a1a", width=1, dash=(4,4))

        # VS badge
        self.arena.create_text(W//2, H//2-10, text="VS",
                               font=tkfont.Font(family="Georgia",size=22,weight="bold"),
                               fill=RED_DIM, tags="vs")

        # Attacker side
        self.arena.create_text(90, 55, text="ATTACKER",
                               font=self.font_coord, fill=GOLD_DIM, tags="albl")
        self.atk_piece_id = self.arena.create_text(90, 130, text="",
                               font=self.font_big, fill=WHITE_TEXT, tags="atk")
        self.atk_name_id  = self.arena.create_text(90, 185, text="",
                               font=self.font_combat, fill=WHITE_TEXT, tags="atkname")
        self.atk_wpn_id   = self.arena.create_text(90, 210, text="",
                               font=self.font_weapon, fill=GOLD, tags="atkwpn")

        # Defender side
        self.arena.create_text(W-90, 55, text="DEFENDER",
                               font=self.font_coord, fill=GOLD_DIM, tags="dlbl")
        self.def_piece_id = self.arena.create_text(W-90, 130, text="",
                               font=self.font_big, fill=WHITE_TEXT, tags="def")
        self.def_name_id  = self.arena.create_text(W-90, 185, text="",
                               font=self.font_combat, fill=WHITE_TEXT, tags="defname")

        # Combat message
        self.combat_msg_id = self.arena.create_text(W//2, H-30, text="",
                               font=self.font_status, fill=GOLD_LIGHT, tags="msg",
                               width=W-40, justify="center")

        # Particle canvas overlay (same size, transparent bg trick via canvas items)
        # We'll draw particles directly on arena canvas

        self._particle_job = None
        self._anim_step = 0

    def _center_overlay(self):
        self.root.update_idletasks()
        rx = self.root.winfo_rootx()
        ry = self.root.winfo_rooty()
        rw = self.root.winfo_width()
        rh = self.root.winfo_height()
        x = rx + rw//2 - self.overlay_w//2
        y = ry + rh//2 - self.overlay_h//2
        self.overlay.geometry(f"{self.overlay_w}x{self.overlay_h}+{x}+{y}")

    # ── Board rendering ────────────────────────────────────────────────────────
    def render_board(self):
        SQ = 68
        for r in range(8):
            for c in range(8):
                sq_name = FILES[c] + str(r+1)
                is_light = (r + c) % 2 != 0
                cv = self.sq_canvas[sq_name]

                # Background color
                if sq_name == self.selected_square:
                    bg = SEL_SQ
                else:
                    bg = LIGHT_SQ if is_light else DARK_SQ

                cv.configure(bg=bg)
                cv.delete("all")

                # Legal move dot / border
                if sq_name in self.legal_targets:
                    piece_here = self.board.piece_at(chess.parse_square(sq_name))
                    if piece_here:
                        # capture target: green border
                        cv.create_rectangle(2, 2, SQ-2, SQ-2,
                                            outline=LEGAL_DOT, width=3)
                    else:
                        # empty: dot
                        cx, cy = SQ//2, SQ//2
                        r2 = 10
                        cv.create_oval(cx-r2, cy-r2, cx+r2, cy+r2,
                                       fill=LEGAL_DOT, outline="", stipple="gray50")

                # Piece glyph
                sq_idx = chess.parse_square(sq_name)
                piece = self.board.piece_at(sq_idx)
                if piece:
                    sym = (WHITE_PIECES if piece.color == chess.WHITE else BLACK_PIECES)[piece.symbol().lower()]
                    text_color = "#ffffff" if piece.color == chess.WHITE else "#1a0a2e"
                    # Shadow color: use the square's own dark tone (no alpha needed)
                    shadow_color = "#3a2010" if (r + c) % 2 != 0 else "#5a3820"

                    # 3-D shadow effect
                    cv.create_text(SQ//2+2, SQ//2+3, text=sym,
                                   font=self.font_piece, fill=shadow_color)
                    cv.create_text(SQ//2, SQ//2, text=sym,
                                   font=self.font_piece, fill=text_color)

        # Status
        if self.board.is_game_over():
            if self.board.is_checkmate():
                winner = "Black" if self.board.turn == chess.WHITE else "White"
                self.gameover_var.set(f"♚ CHECKMATE — {winner} wins! ♚")
            elif self.board.is_stalemate():
                self.gameover_var.set("Draw — Stalemate!")
            else:
                self.gameover_var.set("Draw!")
            self.status_var.set("Game over — start a new game")
        else:
            self.gameover_var.set("")
            turn = "White" if self.board.turn == chess.WHITE else "Black"
            msg = f"{turn}'s turn"
            if self.board.is_check():
                msg += "  ⚠  CHECK!"
            if self.selected_square:
                piece = self.board.piece_at(chess.parse_square(self.selected_square))
                if piece:
                    msg += f"  —  {PIECE_NAMES[piece.symbol().lower()]} selected"
            self.status_var.set(msg)

    # ── Click handling ─────────────────────────────────────────────────────────
    def _on_click(self, sq_name: str):
        if self.animating or self.board.is_game_over():
            return

        sq_idx = chess.parse_square(sq_name)
        piece  = self.board.piece_at(sq_idx)

        if self.selected_square is None:
            # Select own piece
            if piece and piece.color == self.board.turn:
                self.selected_square = sq_name
                moves = list(self.board.legal_moves)
                self.legal_targets = {
                    chess.square_name(m.to_square)
                    for m in moves
                    if m.from_square == sq_idx
                }
                self.render_board()
        else:
            if sq_name == self.selected_square:
                # Deselect
                self.selected_square = None
                self.legal_targets   = set()
                self.render_board()
                return

            # Re-select own piece
            if piece and piece.color == self.board.turn:
                self.selected_square = sq_name
                moves = list(self.board.legal_moves)
                self.legal_targets = {
                    chess.square_name(m.to_square)
                    for m in moves
                    if m.from_square == chess.parse_square(sq_name)
                }
                self.render_board()
                return

            # Attempt move
            if sq_name in self.legal_targets:
                from_sq = chess.parse_square(self.selected_square)
                to_sq   = chess.parse_square(sq_name)

                # Build move (handle promotion)
                promo = None
                moving_piece = self.board.piece_at(from_sq)
                if (moving_piece and moving_piece.piece_type == chess.PAWN and
                        chess.square_rank(to_sq) in (0, 7)):
                    promo = chess.QUEEN

                move = chess.Move(from_sq, to_sq, promotion=promo)

                target_piece = self.board.piece_at(to_sq)

                if target_piece:
                    # Show combat!
                    self.animating = True
                    self._start_combat(moving_piece, target_piece, move)
                else:
                    self.board.push(move)
                    self.selected_square = None
                    self.legal_targets   = set()
                    self.render_board()
            else:
                self.selected_square = None
                self.legal_targets   = set()
                self.render_board()

    # ── Combat animation ───────────────────────────────────────────────────────
    def _start_combat(self, attacker: chess.Piece, defender: chess.Piece, move: chess.Move):
        W, H = self.overlay_w, self.overlay_h
        wpn = WEAPONS[attacker.symbol().lower()]
        atk_sym = (WHITE_PIECES if attacker.color == chess.WHITE else BLACK_PIECES)[attacker.symbol().lower()]
        def_sym = (WHITE_PIECES if defender.color == chess.WHITE else BLACK_PIECES)[defender.symbol().lower()]
        atk_color = "#e8e0c8" if attacker.color == chess.WHITE else "#b090e8"
        def_color = "#e8e0c8" if defender.color == chess.WHITE else "#b090e8"

        # Populate overlay
        self.arena.itemconfig(self.atk_piece_id, text=atk_sym, fill=atk_color)
        self.arena.itemconfig(self.atk_name_id,
                              text=("⬜ " if attacker.color==chess.WHITE else "⬛ ") +
                              PIECE_NAMES[attacker.symbol().lower()])
        self.arena.itemconfig(self.atk_wpn_id, text=wpn["icon"])
        self.arena.itemconfig(self.def_piece_id, text=def_sym, fill=def_color)
        self.arena.itemconfig(self.def_name_id,
                              text=("⬜ " if defender.color==chess.WHITE else "⬛ ") +
                              PIECE_NAMES[defender.symbol().lower()])
        self.arena.itemconfig(self.combat_msg_id,
                              text=f"{PIECE_NAMES[attacker.symbol().lower()]} readies {wpn['name']}...")
        self.arena.delete("particle")

        self._center_overlay()
        self.overlay.deiconify()
        self.overlay.lift()

        self.particles.clear()
        self._anim_step = 0
        self._pending_move = move
        self._wpn_type = wpn["type"]
        self._wpn_color = wpn["color"]

        # Phase timeline (ms): 0=draw weapon, 500=attack+particles, 1000=defender hurt, 1500=defender dies, 2000=close
        self.root.after(500,  self._phase_attack)
        self.root.after(1000, self._phase_hit)
        self.root.after(1500, self._phase_death)
        self.root.after(2100, self._phase_end)

        self._run_particles()

    def _phase_attack(self):
        wpn_type = self._wpn_type
        wpn_color = self._wpn_color
        W, H = self.overlay_w, self.overlay_h

        self.arena.itemconfig(self.combat_msg_id,
                              text=f"{WEAPONS[self.board.piece_at(self._pending_move.from_square).symbol().lower()]['name']} strikes!")

        # Spawn particles based on weapon
        cx, cy = W//2, H//2
        if wpn_type == "sword":
            for _ in range(40):
                a = random.uniform(-math.pi*0.6, math.pi*0.2)
                sp = random.uniform(2, 7)
                self.particles.append(Particle(
                    W//4*1.5, cy,
                    math.cos(a)*sp, math.sin(a)*sp - 1,
                    random.choice(["#e0e080","#ffd040","#ffffff","#c8a030"]),
                    random.uniform(2, 5), random.randint(20, 40), 0.1))
            # Slash line animation
            self._draw_slash(W//4, cy, W*3//4, cy, wpn_color)

        elif wpn_type == "gun":
            # Bullet particles
            for _ in range(25):
                spread = random.uniform(-8, 8)
                sp = random.uniform(8, 14)
                self.particles.append(Particle(
                    W//4, cy + spread,
                    sp, random.uniform(-0.5, 0.5),
                    "#e8e080", random.uniform(1.5, 3), random.randint(8, 18), 0))
            # Muzzle smoke
            for _ in range(20):
                a = random.uniform(-math.pi*0.5, math.pi*0.5) - math.pi
                sp = random.uniform(1, 3)
                self.particles.append(Particle(
                    W//4, cy,
                    math.cos(a)*sp, math.sin(a)*sp,
                    f"#{random.randint(60,100):02x}{random.randint(60,100):02x}{random.randint(60,100):02x}",
                    random.uniform(4, 8), random.randint(15, 30), -0.02))

        elif wpn_type == "cannon":
            for _ in range(80):
                a = random.uniform(0, math.pi*2)
                sp = random.uniform(1, 9)
                color = random.choice(["#ff6020","#ff9040","#ffcc40","#ff4010","#ffffff"])
                self.particles.append(Particle(
                    cx, cy,
                    math.cos(a)*sp, math.sin(a)*sp - 2,
                    color, random.uniform(3, 9), random.randint(20, 50), 0.12))

        elif wpn_type == "magic":
            for i in range(60):
                a = (i / 60) * math.pi * 2
                sp = random.uniform(1, 6)
                color = random.choice(["#c040ff","#8040ff","#ff40ff","#6080ff","#ffffff"])
                self.particles.append(Particle(
                    cx, cy,
                    math.cos(a)*sp, math.sin(a)*sp,
                    color, random.uniform(2, 5), random.randint(25, 45), 0.05))

    def _draw_slash(self, x1, y1, x2, y2, color):
        """Animated diagonal slash line."""
        tag = "slash"
        self.arena.delete(tag)
        steps = 8
        dx = (x2 - x1) / steps
        dy_off = 40
        for i in range(steps):
            xi = x1 + dx * i
            yi = y1 + dy_off * math.sin((i / steps) * math.pi)
            self.arena.create_oval(xi-3, yi-3, xi+3, yi+3,
                                   fill=color, outline="", tags=(tag,"particle"))
        self.root.after(300, lambda: self.arena.delete(tag))

    def _phase_hit(self):
        W, H = self.overlay_w, self.overlay_h
        self.arena.itemconfig(self.combat_msg_id,
                              text=f"{PIECE_NAMES[self.board.piece_at(self._pending_move.to_square).symbol().lower()]} is hit!")
        # Shake defender piece
        self._shake_item(self.def_piece_id, W-90, 130)
        self._shake_item(self.def_name_id,  W-90, 185)

        # Blood / impact particles at defender
        for _ in range(20):
            a = random.uniform(0, math.pi*2)
            sp = random.uniform(1, 4)
            self.particles.append(Particle(
                W-90, 130,
                math.cos(a)*sp, math.sin(a)*sp - 1,
                random.choice(["#e02020","#c01010","#ff4040","#800000"]),
                random.uniform(2, 5), random.randint(15, 30), 0.1))

    def _shake_item(self, item_id, cx, cy, shakes=5, amp=6):
        def _do(n):
            if n <= 0:
                self.arena.coords(item_id, cx, cy)
                return
            ox = random.uniform(-amp, amp)
            oy = random.uniform(-amp*0.5, amp*0.5)
            self.arena.coords(item_id, cx+ox, cy+oy)
            self.root.after(50, lambda: _do(n-1))
        _do(shakes)

    def _phase_death(self):
        self.arena.itemconfig(self.combat_msg_id,
                              text="Defeated! 💀 The piece falls...")
        # Shrink defender piece to nothing
        self._shrink_item(self.def_piece_id)

    def _shrink_item(self, item_id, steps=10, interval=60):
        sizes = [int(48 * (1 - i/steps)) for i in range(steps+1)]
        def _do(idx):
            if idx >= len(sizes): return
            sz = max(sizes[idx], 1)
            try:
                f = tkfont.Font(family="Segoe UI Emoji", size=sz)
                self.arena.itemconfig(item_id, font=f)
            except Exception:
                pass
            if idx < len(sizes)-1:
                self.root.after(interval, lambda: _do(idx+1))
        _do(0)

    def _phase_end(self):
        self.overlay.withdraw()
        # Reset defender piece font
        self.arena.itemconfig(self.def_piece_id, font=self.font_big)
        self.particles.clear()
        if self._particle_job:
            self.root.after_cancel(self._particle_job)
            self._particle_job = None
        self.arena.delete("particle")

        self.board.push(self._pending_move)
        self.selected_square = None
        self.legal_targets   = set()
        self.animating       = False
        self.render_board()

    # ── Particle renderer (runs on tk mainloop via after) ──────────────────────
    def _run_particles(self):
        self.arena.delete("particle")
        alive = []
        for p in self.particles:
            if p.alive:
                p.update()
                alpha_hex = max(10, int(p.alpha * 255))
                # Tkinter doesn't support alpha on canvas ovals natively,
                # so we approximate via stipple patterns
                stipple = ""
                a = p.alpha
                if a < 0.3:   stipple = "gray12"
                elif a < 0.6: stipple = "gray25"
                elif a < 0.8: stipple = "gray50"

                r = max(1, int(p.size * p.alpha))
                try:
                    self.arena.create_oval(
                        p.x - r, p.y - r, p.x + r, p.y + r,
                        fill=p.color, outline="",
                        stipple=stipple if stipple else "",
                        tags="particle")
                except Exception:
                    pass
                alive.append(p)

        self.particles = alive
        if self.animating or self.particles:
            self._particle_job = self.root.after(30, self._run_particles)

    # ── Game controls ──────────────────────────────────────────────────────────
    def new_game(self):
        if self.animating:
            return
        self.overlay.withdraw()
        self.board = chess.Board()
        self.selected_square = None
        self.legal_targets   = set()
        self.animating       = False
        self.particles.clear()
        self.render_board()

    def undo_move(self):
        if self.animating or len(self.board.move_stack) == 0:
            return
        self.board.pop()
        self.selected_square = None
        self.legal_targets   = set()
        self.render_board()


# ─── Entry point ───────────────────────────────────────────────────────────────
def main():
    root = tk.Tk()
    try:
        root.iconbitmap("")      # suppress default icon error on some platforms
    except Exception:
        pass
    app = CombatChess(root)
    root.mainloop()


if __name__ == "__main__":
    main()
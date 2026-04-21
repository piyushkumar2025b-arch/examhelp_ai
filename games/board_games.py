"""
games/board_games.py — Board & Strategy Games (1-7)
1. Tic-Tac-Toe  2. Connect Four  3. Chess  4. Battleship
5. Minesweeper  6. Sudoku  7. 2048
"""
from __future__ import annotations
import streamlit as st
import random
import time
import json
from typing import Optional


def _ai_call(prompt: str, max_tokens: int = 256) -> str:
    try:
        from utils import ai_engine
        return ai_engine.generate(prompt, max_tokens=max_tokens)
    except Exception:
        return ""


def _score_update(game: str, score):
    if "game_scores" not in st.session_state:
        st.session_state.game_scores = {}
    prev = st.session_state.game_scores.get(game, 0)
    if isinstance(score, (int, float)) and score > prev:
        st.session_state.game_scores[game] = score


# ═══════════════════════════════════════════
# 1. TIC-TAC-TOE
# ═══════════════════════════════════════════
def _ttt_winner(b):
    for (a,bb,c) in [(0,1,2),(3,4,5),(6,7,8),(0,3,6),(1,4,7),(2,5,8),(0,4,8),(2,4,6)]:
        if b[a] and b[a]==b[bb]==b[c]: return b[a]
    if all(b): return "Draw"
    return None

def _ttt_minimax(b, maxi, alpha=-1e9, beta=1e9):
    w = _ttt_winner(b)
    if w == "O": return 10
    if w == "X": return -10
    if w == "Draw": return 0
    if maxi:
        best = -1e9
        for i in range(9):
            if not b[i]:
                b[i]="O"; best=max(best,_ttt_minimax(b,False,alpha,beta)); b[i]=""
                alpha=max(alpha,best)
                if beta<=alpha: break
        return best
    else:
        best = 1e9
        for i in range(9):
            if not b[i]:
                b[i]="X"; best=min(best,_ttt_minimax(b,True,alpha,beta)); b[i]=""
                beta=min(beta,best)
                if beta<=alpha: break
        return best

def _ttt_ai_move(b):
    best, move = -1e9, -1
    for i in range(9):
        if not b[i]:
            b[i]="O"; s=_ttt_minimax(b,False); b[i]=""
            if s>best: best,move = s,i
    return move

def render_tictactoe():
    st.markdown('<div style="font-size:1.4rem;font-weight:900;color:#a5b4fc;margin-bottom:10px;">🎮 Tic-Tac-Toe vs AI</div><div style="color:#64748b;font-size:.85rem;margin-bottom:14px;">You are ✅ X · AI is ❌ O · AI uses Minimax — it never loses!</div>', unsafe_allow_html=True)
    if "ttt_b" not in st.session_state: st.session_state.ttt_b=[""]* 9; st.session_state.ttt_over=False; st.session_state.ttt_sc={"X":0,"O":0,"Draw":0}
    b=st.session_state.ttt_b
    sc=st.session_state.ttt_sc
    c1,c2,c3=st.columns(3)
    for col,lbl,val in zip([c1,c2,c3],["You (X)","AI (O)","Draws"],[sc["X"],sc["O"],sc["Draw"]]):
        col.metric(lbl,val)
    st.markdown("---")
    w=_ttt_winner(b); over=w or st.session_state.ttt_over
    for row in range(3):
        cols=st.columns(3)
        for col in range(3):
            idx=row*3+col
            cell=b[idx]
            emoji={"X":"✅","O":"❌","":" "}[cell]
            if cols[col].button(emoji,key=f"ttt_{idx}",use_container_width=True,disabled=bool(cell) or bool(over)):
                b[idx]="X"
                if not _ttt_winner(b):
                    ai=_ttt_ai_move(b)
                    if ai>=0: b[ai]="O"
                st.session_state.ttt_b=b; st.rerun()
    w=_ttt_winner(b)
    if w:
        if w=="X": st.success("🎉 You Win!"); st.balloons(); _score_update("Tic-Tac-Toe",1)
        elif w=="O": st.error("🤖 AI Wins!")
        else: st.info("🤝 Draw!")
        st.session_state.ttt_sc[w]=st.session_state.ttt_sc.get(w,0)+1
        st.session_state.ttt_over=True
    if st.button("🔄 New Game",use_container_width=True,key="ttt_new"):
        st.session_state.ttt_b=[""]* 9; st.session_state.ttt_over=False; st.rerun()


# ═══════════════════════════════════════════
# 2. CONNECT FOUR
# ═══════════════════════════════════════════
def _c4_check(b):
    R,C=6,7
    def _check_dir(r,c,dr,dc,p):
        count=0
        for _ in range(4):
            if 0<=r<R and 0<=c<C and b[r][c]==p: count+=1; r+=dr; c+=dc
            else: break
        return count==4
    for r in range(R):
        for c in range(C):
            if b[r][c]!=0:
                p=b[r][c]
                for dr,dc in [(0,1),(1,0),(1,1),(1,-1)]:
                    if _check_dir(r,c,dr,dc,p): return p
    return None

def _c4_drop(b,col,player):
    for r in range(5,-1,-1):
        if b[r][col]==0: b[r][col]=player; return True
    return False

def _c4_ai_move(b):
    R,C=6,7
    def score_col(col,p):
        s=0
        for r in range(R):
            if b[r][col]==0:
                b[r][col]=p
                for dr,dc in [(0,1),(1,0),(1,1),(1,-1)]:
                    cnt=sum(1 for k in range(4) if 0<=r+k*dr<R and 0<=col+k*dc<C and b[r+k*dr][col+k*dc]==p)
                    s+=cnt**2
                b[r][col]=0; break
        return s
    # block win first
    for col in range(C):
        for r in range(5,-1,-1):
            if b[r][col]==0:
                b[r][col]=1
                if _c4_check(b): b[r][col]=0; return col
                b[r][col]=0; break
    scores=[(score_col(c,2)-score_col(c,1),c) for c in range(C) if any(b[r][c]==0 for r in range(R))]
    if not scores: return 0
    return max(scores)[1]

def render_connect_four():
    st.markdown('<div style="font-size:1.4rem;font-weight:900;color:#fde68a;margin-bottom:10px;">🔴 Connect Four</div><div style="color:#64748b;font-size:.85rem;margin-bottom:14px;">You are 🔴 · AI is 🟡 · Drop pieces, connect 4 to win!</div>', unsafe_allow_html=True)
    if "c4_b" not in st.session_state:
        st.session_state.c4_b=[[0]*7 for _ in range(6)]; st.session_state.c4_over=False; st.session_state.c4_msg=""
    b=st.session_state.c4_b
    cell_map={0:"⚫",1:"🔴",2:"🟡"}
    # Column buttons
    if not st.session_state.c4_over:
        cols=st.columns(7)
        for col_idx in range(7):
            with cols[col_idx]:
                if st.button(f"↓",key=f"c4_col_{col_idx}",use_container_width=True):
                    if _c4_drop(b,col_idx,1):
                        if _c4_check(b)==1: st.session_state.c4_msg="🔴 You Win!"; st.session_state.c4_over=True; _score_update("Connect Four",1)
                        elif all(b[0][c]!=0 for c in range(7)): st.session_state.c4_msg="🤝 Draw!"; st.session_state.c4_over=True
                        else:
                            ai=_c4_ai_move(b)
                            _c4_drop(b,ai,2)
                            if _c4_check(b)==2: st.session_state.c4_msg="🟡 AI Wins!"; st.session_state.c4_over=True
                    st.session_state.c4_b=b; st.rerun()
    # Board display
    html='<table style="border-collapse:collapse;margin:0 auto;">'
    for row in b:
        html+="<tr>"+"".join(f'<td style="font-size:1.6rem;padding:1px;">{cell_map[c]}</td>' for c in row)+"</tr>"
    html+="</table>"
    st.markdown(html,unsafe_allow_html=True)
    if st.session_state.c4_msg:
        st.markdown(f"### {st.session_state.c4_msg}")
        if "Win" in st.session_state.c4_msg and "🔴" in st.session_state.c4_msg: st.balloons()
    if st.button("🔄 New Game",use_container_width=True,key="c4_new"):
        del st.session_state.c4_b,st.session_state.c4_over,st.session_state.c4_msg; st.rerun()


# ═══════════════════════════════════════════
# 3. CHESS
# ═══════════════════════════════════════════
def render_chess():
    st.markdown('<div style="font-size:1.4rem;font-weight:900;color:#34d399;margin-bottom:10px;">♟️ Chess vs AI</div>', unsafe_allow_html=True)
    try:
        import chess, chess.svg, base64
    except ImportError:
        st.warning("Install python-chess: `pip install chess`")
        return
    if "chess_board" not in st.session_state:
        st.session_state.chess_board=chess.Board(); st.session_state.chess_history=[]; st.session_state.chess_msg=""
    board=st.session_state.chess_board
    # Render board
    svg=chess.svg.board(board,size=360)
    b64=base64.b64encode(svg.encode()).decode()
    st.markdown(f'<div style="text-align:center"><img src="data:image/svg+xml;base64,{b64}" width="360"/></div>',unsafe_allow_html=True)
    if st.session_state.chess_msg:
        st.info(st.session_state.chess_msg)
    if not board.is_game_over():
        if board.turn==chess.WHITE:
            move_str=st.text_input("Your move (UCI, e.g. e2e4):",key=f"chess_input_{len(st.session_state.chess_history)}",placeholder="e2e4")
            if st.button("▶ Make Move",key="chess_move_btn",type="primary"):
                try:
                    move=chess.Move.from_uci(move_str.strip())
                    if move in board.legal_moves:
                        board.push(move); st.session_state.chess_history.append(str(move))
                        # AI move
                        if not board.is_game_over():
                            VALS={chess.QUEEN:9,chess.ROOK:5,chess.BISHOP:3,chess.KNIGHT:3,chess.PAWN:1}
                            best_mv,best_sc=None,-999
                            for mv in board.legal_moves:
                                sc=0
                                if board.is_capture(mv): captured=board.piece_at(mv.to_square); sc=VALS.get(captured.piece_type,0) if captured else 0
                                if sc>best_sc: best_sc,best_mv=sc,mv
                            if best_mv is None: best_mv=random.choice(list(board.legal_moves))
                            board.push(best_mv); st.session_state.chess_history.append(str(best_mv))
                        st.session_state.chess_board=board; st.rerun()
                    else: st.error("Illegal move!")
                except Exception: st.error("Invalid move format.")
    else:
        result=board.result()
        msg=f"Game Over! Result: {result}"
        if result=="1-0": msg+=" — You Win! 🏆"; _score_update("Chess",1)
        elif result=="0-1": msg+=" — AI Wins 🤖"
        else: msg+=" — Draw 🤝"
        st.success(msg)
    if st.session_state.chess_history:
        with st.expander(f"📜 Move History ({len(st.session_state.chess_history)} moves)"):
            st.write(" | ".join(st.session_state.chess_history))
    if st.button("🔄 New Game",use_container_width=True,key="chess_new"):
        del st.session_state.chess_board,st.session_state.chess_history,st.session_state.chess_msg; st.rerun()


# ═══════════════════════════════════════════
# 4. BATTLESHIP
# ═══════════════════════════════════════════
def _bs_init():
    SHIPS=[5,4,3,3,2]
    def place_ships():
        grid=[[0]*10 for _ in range(10)]
        for sz in SHIPS:
            placed=False
            while not placed:
                h=random.choice([True,False]); r=random.randint(0,9); c=random.randint(0,9)
                cells=[(r,c+i) if h else (r+i,c) for i in range(sz)]
                if all(0<=rr<10 and 0<=cc<10 and grid[rr][cc]==0 for rr,cc in cells):
                    for rr,cc in cells: grid[rr][cc]=1
                    placed=True
        return grid
    st.session_state.bs_player=place_ships(); st.session_state.bs_ai=place_ships()
    st.session_state.bs_player_hits=[[False]*10 for _ in range(10)]
    st.session_state.bs_ai_hits=[[False]*10 for _ in range(10)]
    st.session_state.bs_ai_hunt=[]; st.session_state.bs_ai_target=[]
    st.session_state.bs_over=False; st.session_state.bs_msg=""; st.session_state.bs_turn="player"

def _bs_ai_shot(player_grid,player_hits):
    if st.session_state.bs_ai_target:
        r,c=st.session_state.bs_ai_target.pop(0)
        while player_hits[r][c] and st.session_state.bs_ai_target:
            r,c=st.session_state.bs_ai_target.pop(0)
    else:
        while True:
            r,c=random.randint(0,9),random.randint(0,9)
            if not player_hits[r][c]: break
    player_hits[r][c]=True
    if player_grid[r][c]==1:
        for dr,dc in [(-1,0),(1,0),(0,-1),(0,1)]:
            nr,nc=r+dr,c+dc
            if 0<=nr<10 and 0<=nc<10 and not player_hits[nr][nc]:
                st.session_state.bs_ai_target.append((nr,nc))

def render_battleship():
    st.markdown('<div style="font-size:1.4rem;font-weight:900;color:#60a5fa;margin-bottom:10px;">⚓ Battleship</div>', unsafe_allow_html=True)
    if "bs_player" not in st.session_state: _bs_init()
    pg=st.session_state.bs_player; ag=st.session_state.bs_ai
    ph=st.session_state.bs_player_hits; ah=st.session_state.bs_ai_hits
    def render_grid(grid,hits,show_ships,label):
        st.markdown(f"**{label}**")
        html='<table style="border-collapse:collapse;">'
        for r in range(10):
            html+="<tr>"
            for c in range(10):
                if hits[r][c]:
                    cell="💥" if grid[r][c]==1 else "❌"
                elif show_ships and grid[r][c]==1:
                    cell="🚢"
                else: cell="🌊"
                html+=f'<td style="font-size:1rem;padding:0;">{cell}</td>'
            html+="</tr>"
        html+="</table>"
        st.markdown(html,unsafe_allow_html=True)
    col_p,col_a=st.columns(2)
    with col_p: render_grid(pg,ph,True,"🛡 Your Fleet")
    with col_a: render_grid(ag,ah,False,"🎯 Enemy Waters — Click to Attack")
    if not st.session_state.bs_over:
        st.markdown("**Your turn — pick a target (row 0-9, col 0-9):**")
        rc1,rc2=st.columns(2)
        tr=rc1.number_input("Row",0,9,key="bs_r")
        tc=rc2.number_input("Col",0,9,key="bs_c")
        if st.button("🎯 Fire!",type="primary",use_container_width=True,key="bs_fire"):
            r,c=int(tr),int(tc)
            if ah[r][c]: st.warning("Already shot there!")
            else:
                ah[r][c]=True
                if all(ah[r][c] for r in range(10) for c in range(10) if ag[r][c]==1):
                    st.session_state.bs_over=True; st.session_state.bs_msg="🎉 You sank all enemy ships!"; _score_update("Battleship",1)
                else:
                    _bs_ai_shot(pg,ph)
                    if all(ph[r][c] for r in range(10) for c in range(10) if pg[r][c]==1):
                        st.session_state.bs_over=True; st.session_state.bs_msg="💀 AI sank your fleet!"
                st.rerun()
    if st.session_state.bs_msg: st.info(st.session_state.bs_msg)
    if st.button("🔄 New Game",use_container_width=True,key="bs_new"): _bs_init(); st.rerun()


# ═══════════════════════════════════════════
# 5. MINESWEEPER
# ═══════════════════════════════════════════
def _ms_init(rows=9,cols=9,mines=10):
    grid=[[0]*cols for _ in range(rows)]; flags=[[False]*cols for _ in range(rows)]
    revealed=[[False]*cols for _ in range(rows)]
    mine_set=set()
    while len(mine_set)<mines:
        mine_set.add((random.randint(0,rows-1),random.randint(0,cols-1)))
    for r,c in mine_set: grid[r][c]=-1
    for r in range(rows):
        for c in range(cols):
            if grid[r][c]!=-1:
                grid[r][c]=sum(1 for dr in[-1,0,1] for dc in[-1,0,1] if (r+dr,c+dc) in mine_set)
    st.session_state.ms_grid=grid; st.session_state.ms_flags=flags; st.session_state.ms_revealed=revealed
    st.session_state.ms_over=False; st.session_state.ms_won=False; st.session_state.ms_mines=mine_set
    st.session_state.ms_start=None

def _ms_cascade(r,c,grid,revealed):
    R,C=len(grid),len(grid[0])
    stack=[(r,c)]
    while stack:
        rr,cc=stack.pop()
        if not(0<=rr<R and 0<=cc<C) or revealed[rr][cc]: continue
        revealed[rr][cc]=True
        if grid[rr][cc]==0:
            for dr in[-1,0,1]:
                for dc in[-1,0,1]:
                    if dr==0 and dc==0: continue
                    stack.append((rr+dr,cc+dc))

def render_minesweeper():
    st.markdown('<div style="font-size:1.4rem;font-weight:900;color:#fb923c;margin-bottom:10px;">💣 Minesweeper</div>', unsafe_allow_html=True)
    if "ms_grid" not in st.session_state: _ms_init()
    grid=st.session_state.ms_grid; flags=st.session_state.ms_flags; revealed=st.session_state.ms_revealed
    R,C=9,9
    NUM_COLORS=["","#3b82f6","#22c55e","#ef4444","#1e40af","#991b1b","#0891b2","#000","#6b7280"]
    toggle_flag=st.checkbox("🚩 Flag Mode (click to place/remove flag)",key="ms_flag_mode")
    html='<table style="border-collapse:collapse;">'
    for r in range(R):
        html+="<tr>"
        for c in range(C):
            if revealed[r][c]:
                val=grid[r][c]
                if val==-1: cell='💥'
                elif val==0: cell='<td style="width:28px;height:28px;background:#1e293b;border:1px solid #334;"></td>'; html+=cell; continue
                else: cell=f'<td style="width:28px;height:28px;background:#1e293b;border:1px solid #334;text-align:center;vertical-align:middle;font-weight:900;color:{NUM_COLORS[val]};font-size:.85rem;">{val}</td>'; html+=cell; continue
            elif flags[r][c]: cell="🚩"
            else: cell="⬜"
            html+=f'<td style="width:28px;height:28px;background:#0f172a;border:1px solid #334;text-align:center;vertical-align:middle;font-size:1rem;">{cell}</td>'
        html+="</tr>"
    html+="</table>"
    st.markdown(html,unsafe_allow_html=True)
    if not st.session_state.ms_over:
        cr=st.number_input("Row",0,8,key="ms_r"); cc=st.number_input("Col",0,8,key="ms_c")
        if toggle_flag:
            if st.button("🚩 Toggle Flag",use_container_width=True,key="ms_flag_btn"):
                if not revealed[cr][cc]: flags[cr][cc]=not flags[cr][cc]; st.rerun()
        else:
            if st.button("🖱 Reveal Cell",type="primary",use_container_width=True,key="ms_reveal"):
                if not flags[cr][cc] and not revealed[cr][cc]:
                    if st.session_state.ms_start is None: st.session_state.ms_start=time.time()
                    if grid[cr][cc]==-1:
                        revealed[cr][cc]=True; st.session_state.ms_over=True
                        for r,c in st.session_state.ms_mines: revealed[r][c]=True
                    else:
                        _ms_cascade(cr,cc,grid,revealed)
                        non_mine=sum(1 for r in range(R) for c in range(C) if grid[r][c]!=-1)
                        rev=sum(1 for r in range(R) for c in range(C) if revealed[r][c] and grid[r][c]!=-1)
                        if rev==non_mine: st.session_state.ms_won=True; st.session_state.ms_over=True
                    st.rerun()
    if st.session_state.ms_over:
        if st.session_state.ms_won: st.success("🎉 You cleared the minefield!"); st.balloons(); _score_update("Minesweeper",1)
        else: st.error("💥 Boom! You hit a mine!")
    if st.button("🔄 New Game",use_container_width=True,key="ms_new"): _ms_init(); st.rerun()


# ═══════════════════════════════════════════
# 6. SUDOKU
# ═══════════════════════════════════════════
SUDOKU_PUZZLES = [
    # Easy
    [[5,3,0,0,7,0,0,0,0],[6,0,0,1,9,5,0,0,0],[0,9,8,0,0,0,0,6,0],
     [8,0,0,0,6,0,0,0,3],[4,0,0,8,0,3,0,0,1],[7,0,0,0,2,0,0,0,6],
     [0,6,0,0,0,0,2,8,0],[0,0,0,4,1,9,0,0,5],[0,0,0,0,8,0,0,7,9]],
    # Medium
    [[0,2,0,6,0,8,0,0,0],[5,8,0,0,0,9,7,0,0],[0,0,0,0,4,0,0,0,0],
     [3,7,0,0,0,0,5,0,0],[6,0,0,0,0,0,0,0,4],[0,0,8,0,0,0,0,1,3],
     [0,0,0,0,2,0,0,0,0],[0,0,9,8,0,0,0,3,6],[0,0,0,3,0,6,0,9,0]],
]
SUDOKU_SOLUTIONS = [
    [[5,3,4,6,7,8,9,1,2],[6,7,2,1,9,5,3,4,8],[1,9,8,3,4,2,5,6,7],
     [8,5,9,7,6,1,4,2,3],[4,2,6,8,5,3,7,9,1],[7,1,3,9,2,4,8,5,6],
     [9,6,1,5,3,7,2,8,4],[2,8,7,4,1,9,6,3,5],[3,4,5,2,8,6,1,7,9]],
    [[1,2,3,6,7,8,9,4,5],[5,8,4,2,3,9,7,6,1],[9,6,7,1,4,5,3,2,8],
     [3,7,2,4,6,1,5,8,9],[6,9,1,5,8,3,2,7,4],[4,5,8,7,9,2,6,1,3],
     [1,3,5,9,2,6,4,8,7],[2,4,9,8,1,7,8,3,6],[8,7,6,3,5,6,1,9,2]],
]

def render_sudoku():
    st.markdown('<div style="font-size:1.4rem;font-weight:900;color:#c4b5fd;margin-bottom:10px;">🔢 Sudoku</div>', unsafe_allow_html=True)
    if "sdk_idx" not in st.session_state: st.session_state.sdk_idx=0; st.session_state.sdk_board=None; st.session_state.sdk_msg=""
    idx=st.session_state.sdk_idx
    puzzle=SUDOKU_PUZZLES[idx % len(SUDOKU_PUZZLES)]
    sol=SUDOKU_SOLUTIONS[idx % len(SUDOKU_SOLUTIONS)]
    if st.session_state.sdk_board is None:
        st.session_state.sdk_board=[row[:] for row in puzzle]
    board=st.session_state.sdk_board
    st.selectbox("Puzzle",["Easy","Medium"],key="sdk_level",on_change=lambda:setattr(st.session_state,"sdk_board",None))
    # Render 9x9 grid
    st.markdown('<div style="font-size:.75rem;color:#64748b;">Fill in the blanks (1-9):</div>',unsafe_allow_html=True)
    for r in range(9):
        cols=st.columns(9)
        for c in range(9):
            if puzzle[r][c]!=0:
                cols[c].markdown(f'<div style="text-align:center;font-weight:900;color:#a5b4fc;padding:6px;">{puzzle[r][c]}</div>',unsafe_allow_html=True)
            else:
                val=cols[c].number_input(" ",0,9,value=board[r][c],key=f"sdk_{r}_{c}",label_visibility="collapsed")
                board[r][c]=val
    bc1,bc2,bc3=st.columns(3)
    if bc1.button("✅ Check",use_container_width=True,key="sdk_check"):
        err=[]
        for r in range(9):
            for c in range(9):
                if board[r][c] and board[r][c]!=sol[r][c]: err.append((r,c))
        st.session_state.sdk_msg=f"✅ All correct!" if not err else f"❌ {len(err)} error(s) found."
    if bc2.button("💡 Hint",use_container_width=True,key="sdk_hint"):
        with st.spinner("Getting hint..."):
            prompt=f"Sudoku board JSON: {json.dumps(board)}. Give one logical next move. Reply: 'Row X, Col Y should be Z because...'"
            h=_ai_call(prompt,256)
            st.session_state.sdk_msg=h or "AI hint unavailable."
    if bc3.button("🔓 Solve",use_container_width=True,key="sdk_solve"):
        st.session_state.sdk_board=[row[:] for row in sol]; st.rerun()
    if st.session_state.sdk_msg: st.info(st.session_state.sdk_msg)
    if st.button("🔄 New Puzzle",use_container_width=True,key="sdk_new"):
        st.session_state.sdk_idx+=1; st.session_state.sdk_board=None; st.session_state.sdk_msg=""; st.rerun()


# ═══════════════════════════════════════════
# 7. 2048
# ═══════════════════════════════════════════
def _2048_spawn(grid):
    empty=[(r,c) for r in range(4) for c in range(4) if grid[r][c]==0]
    if empty:
        r,c=random.choice(empty)
        grid[r][c]=random.choices([2,4],weights=[9,1])[0]

def _2048_slide_row(row):
    row=[x for x in row if x]; score=0
    i=0
    while i<len(row)-1:
        if row[i]==row[i+1]: row[i]*=2; score+=row[i]; row.pop(i+1)
        i+=1
    row+=[0]*(4-len(row)); return row,score

def _2048_move(grid,direction):
    score=0; moved=False
    orig=[row[:] for row in grid]
    if direction in("left","right"):
        for r in range(4):
            row=grid[r] if direction=="left" else grid[r][::-1]
            nr,sc=_2048_slide_row(row); score+=sc
            grid[r]=nr if direction=="left" else nr[::-1]
    else:
        for c in range(4):
            col=[grid[r][c] for r in range(4)]
            if direction=="down": col=col[::-1]
            nc,sc=_2048_slide_row(col); score+=sc
            if direction=="down": nc=nc[::-1]
            for r in range(4): grid[r][c]=nc[r]
    moved=grid!=orig; return score,moved

TILE_COLORS={0:"#1e293b",2:"#eee4da",4:"#ede0c8",8:"#f2b179",16:"#f59563",32:"#f67c5f",64:"#f65e3b",128:"#edcf72",256:"#edcc61",512:"#edc850",1024:"#edc53f",2048:"#edc22e"}

def render_2048():
    st.markdown('<div style="font-size:1.4rem;font-weight:900;color:#fb923c;margin-bottom:10px;">🎯 2048</div><div style="color:#64748b;font-size:.85rem;margin-bottom:10px;">Type W/A/S/D and press Move to slide tiles. Merge same tiles to reach 2048!</div>', unsafe_allow_html=True)
    if "g2048_grid" not in st.session_state:
        g=[[0]*4 for _ in range(4)]; _2048_spawn(g); _2048_spawn(g)
        st.session_state.g2048_grid=g; st.session_state.g2048_score=0; st.session_state.g2048_over=False
    grid=st.session_state.g2048_grid
    # Render board
    html='<table style="border-collapse:separate;border-spacing:4px;margin:0 auto;">'
    for row in grid:
        html+="<tr>"
        for val in row:
            clr=TILE_COLORS.get(val,"#3d3a2e")
            txt_c="#776e65" if val<=4 else "#f9f6f2"
            html+=f'<td style="width:60px;height:60px;background:{clr};border-radius:6px;text-align:center;vertical-align:middle;font-size:{"1.2rem" if val<1000 else ".9rem"};font-weight:900;color:{txt_c};">{val if val else ""}</td>'
        html+="</tr>"
    html+="</table>"
    st.markdown(html,unsafe_allow_html=True)
    st.markdown(f"**Score: {st.session_state.g2048_score}**")
    move_input=st.text_input("Direction (W=up A=left S=down D=right):","",max_chars=1,key=f"g2048_dir_{st.session_state.g2048_score}").upper()
    dir_map={"W":"up","A":"left","S":"down","D":"right"}
    if st.button("▶ Move",type="primary",use_container_width=True,key="g2048_move"):
        if move_input in dir_map:
            sc,moved=_2048_move(grid,dir_map[move_input])
            st.session_state.g2048_score+=sc
            if moved: _2048_spawn(grid)
            _score_update("2048",st.session_state.g2048_score)
            if any(2048 in row for row in grid): st.session_state.g2048_over=True
            st.session_state.g2048_grid=grid; st.rerun()
    if st.session_state.g2048_over: st.success("🎉 You reached 2048!"); st.balloons()
    if st.button("🔄 New Game",use_container_width=True,key="g2048_new"):
        del st.session_state.g2048_grid,st.session_state.g2048_score,st.session_state.g2048_over; st.rerun()

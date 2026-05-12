import React from 'react';
import './KillAnimation.css';

// Unicode mapping for chess pieces
const pieceUnicode = {
  w: { p: '♙', n: '♘', b: '♗', r: '♖', q: '♕', k: '♔' },
  b: { p: '♟', n: '♞', b: '♝', r: '♜', q: '♛', k: '♚' }
};

const pieceNames = {
  p: 'Pawn', n: 'Knight', b: 'Bishop', r: 'Rook', q: 'Queen', k: 'King'
};

export default function KillAnimation({ attacker, victim, color }) {
  const attackerColor = color;
  const victimColor = color === 'w' ? 'b' : 'w';

  const attackerChar = pieceUnicode[attackerColor][attacker];
  const victimChar = pieceUnicode[victimColor][victim];
  const attackerName = pieceNames[attacker];

  return (
    <div className="kill-screen-overlay">
      <div className="kill-content">
        <h1 className="impostor-text">
          {attackerName.toUpperCase()} WAS THE IMPOSTOR
        </h1>
        
        {/* CSS Sprite Battle Scene */}
        <div className="battle-scene">
          
          <div className="sprite attacker-sprite">
            {attackerChar}
            <div className="knife">🗡️</div>
          </div>
          
          <div className="sprite victim-sprite">
            {victimChar}
            <div className="ghost">👻</div>
          </div>

        </div>
      </div>
    </div>
  );
}
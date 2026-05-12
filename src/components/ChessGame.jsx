import { useState, useRef } from 'react';
import { Chess } from 'chess.js';
import { Chessboard } from 'react-chessboard';
import KillAnimation from './KillAnimation';

export default function ChessGame() {
  // 1. useRef keeps the chess engine intact. It will never accidentally reset or lose data.
  const gameRef = useRef(new Chess());
  
  // 2. We only use state for the FEN string (which tells the board what to draw)
  const [fen, setFen] = useState(gameRef.current.fen());
  const [killEvent, setKillEvent] = useState(null);
  const [moveFrom, setMoveFrom] = useState(null);

  // 3. The master move executor
  function executeMove(move) {
    let moveResult = null;
    
    try {
      // Apply the move directly to our background engine
      moveResult = gameRef.current.move(move);
    } catch (e) {
      // Move was illegal (chess.js throws an error here)
      return null; 
    }

    // If the move was valid...
    if (moveResult) {
      // Sync the visual board with the background engine
      setFen(gameRef.current.fen());

      // Trigger the Kill Screen if a piece was captured!
      if (moveResult.captured) {
        setKillEvent({
          attacker: moveResult.piece,
          victim: moveResult.captured,
          attackerColor: moveResult.color
        });

        setTimeout(() => {
          setKillEvent(null);
        }, 2500);
      }
    }
    
    return moveResult;
  }

  // --- INTERACTION HANDLERS ---

  function onDrop(sourceSquare, targetSquare) {
    if (killEvent) return false;

    const moveResult = executeMove({
      from: sourceSquare,
      to: targetSquare,
      promotion: 'q', // Always promote to queen
    });

    setMoveFrom(null); 
    return moveResult !== null; // Board needs true/false to know if it should snap the piece back
  }

  function onSquareClick(square) {
    if (killEvent) return;

    if (!moveFrom) {
      const pieceOnSquare = gameRef.current.get(square);
      if (pieceOnSquare && pieceOnSquare.color === gameRef.current.turn()) {
        setMoveFrom(square);
      }
      return;
    }

    const moveResult = executeMove({
      from: moveFrom,
      to: square,
      promotion: 'q'
    });

    if (!moveResult) {
      const pieceOnSquare = gameRef.current.get(square);
      if (pieceOnSquare && pieceOnSquare.color === gameRef.current.turn()) {
        setMoveFrom(square);
      } else {
        setMoveFrom(null);
      }
    } else {
      setMoveFrom(null);
    }
  }

  return (
    <div style={{ position: 'relative', width: '500px', margin: '0 auto', marginTop: '50px' }}>
      <h2 style={{ textAlign: 'center', fontFamily: 'monospace' }}>SUS CHESS</h2>
      
      <Chessboard 
        position={fen} // The board reads the FEN string from state
        onPieceDrop={onDrop} 
        onSquareClick={onSquareClick}
        boardWidth={500}
        animationDuration={killEvent ? 0 : 300}
        customSquareStyles={moveFrom ? { [moveFrom]: { backgroundColor: 'rgba(255, 255, 0, 0.5)' } } : {}}
      />

      {killEvent && (
        <KillAnimation 
          attacker={killEvent.attacker} 
          victim={killEvent.victim} 
          color={killEvent.attackerColor} 
        />
      )}
    </div>
  );
}
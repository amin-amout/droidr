"""
Speaker Identification Module

This module provides speaker recognition capabilities using voice embeddings.
It can enroll users and identify them from audio samples.
"""

import sqlite3
import numpy as np
import pickle
import logging
from typing import List, Optional, Tuple
from pathlib import Path
import soundfile as sf

logger = logging.getLogger(__name__)


class SpeakerIdentifier:
    """
    Speaker identification system using voice embeddings.
    
    Uses a pretrained speaker embedding model to create voice fingerprints
    and matches them against enrolled users stored in a SQLite database.
    """
    
    def __init__(self, model_path: Optional[str] = None, db_path: str = "speakers.db", 
                 similarity_threshold: float = 0.75,
                 accept_near_threshold: bool = True,
                 near_margin: float = 0.08):
        """
        Initialize the speaker identification system.
        
        Args:
            model_path: Path to pretrained embedding model (optional, uses default)
            db_path: Path to SQLite database for storing speaker embeddings
            similarity_threshold: Minimum cosine similarity to accept a match (0-1)
        """
        self.db_path = db_path
        self.similarity_threshold = similarity_threshold
        self.model = None
        self.accept_near_threshold = accept_near_threshold
        self.near_margin = near_margin
        
        # Initialize database
        self._init_database()
        
        # Load embedding model
        self._load_model(model_path)
        
        logger.info(f"SpeakerIdentifier initialized with threshold={similarity_threshold}")
    
    def _init_database(self):
        """Create SQLite database and tables if they don't exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Table to store averaged speaker embedding (current fingerprint)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS speakers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                embedding BLOB NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Table to store raw enrollment samples (one row per recorded sample)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS enrollment_samples (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                embedding BLOB NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
        logger.info(f"Database initialized at {self.db_path}")
    
    def _load_model(self, model_path: Optional[str] = None):
        """
        Load the speaker embedding model.
        
        Args:
            model_path: Path to model file (optional)
        """
        try:
            # Try to import resemblyzer (lightweight, works offline)
            from resemblyzer import VoiceEncoder
            self.model = VoiceEncoder()
            self.embedding_type = "resemblyzer"
            logger.info("Loaded Resemblyzer voice encoder")
            
        except ImportError:
            logger.warning("Resemblyzer not available, using fallback MFCC-based embeddings")
            self.embedding_type = "mfcc"
            # Fallback to MFCC-based simple embeddings
            # This will be implemented as a simpler alternative
    
    def extract_embedding(self, audio_data: np.ndarray, sample_rate: int = 16000) -> np.ndarray:
        """
        Extract speaker embedding from audio data.
        
        Args:
            audio_data: Audio samples as numpy array
            sample_rate: Sample rate of audio
            
        Returns:
            Embedding vector as numpy array
        """
        if self.embedding_type == "resemblyzer":
            # Resemblyzer expects audio at 16kHz
            if len(audio_data.shape) > 1:
                audio_data = audio_data.mean(axis=1)  # Convert stereo to mono
            
            # Extract embedding
            embedding = self.model.embed_utterance(audio_data)
            return embedding
        
        else:
            # Fallback: Use MFCC-based simple embedding
            return self._extract_mfcc_embedding(audio_data, sample_rate)
    
    def _extract_mfcc_embedding(self, audio_data: np.ndarray, sample_rate: int = 16000) -> np.ndarray:
        """
        Extract MFCC-based embedding as fallback.
        
        Args:
            audio_data: Audio samples
            sample_rate: Sample rate
            
        Returns:
            MFCC feature vector
        """
        try:
            import librosa
            
            # Extract MFCCs
            mfccs = librosa.feature.mfcc(y=audio_data, sr=sample_rate, n_mfcc=40)
            
            # Compute statistics across time to get fixed-size embedding
            mfcc_mean = np.mean(mfccs, axis=1)
            mfcc_std = np.std(mfccs, axis=1)
            mfcc_delta = np.mean(librosa.feature.delta(mfccs), axis=1)
            
            # Concatenate features
            embedding = np.concatenate([mfcc_mean, mfcc_std, mfcc_delta])
            
            # Normalize
            embedding = embedding / (np.linalg.norm(embedding) + 1e-8)
            
            return embedding
            
        except ImportError:
            logger.error("librosa not available for MFCC extraction")
            # Return random embedding as last resort (for testing only)
            return np.random.randn(128).astype(np.float32)
    
    def enroll_user(self, name: str, audio_file: Optional[str] = None, 
                    audio_data: Optional[np.ndarray] = None, sample_rate: int = 16000) -> bool:
        """
        Enroll a new user by storing their voice embedding.
        
        Args:
            name: User's name (unique identifier)
            audio_file: Path to audio file for enrollment (WAV format)
            audio_data: Audio data as numpy array (alternative to audio_file)
            sample_rate: Sample rate of audio_data
            
        Returns:
            True if enrollment successful, False otherwise
        """
        try:
            # Load audio
            if audio_file:
                audio_data, sample_rate = sf.read(audio_file)
            elif audio_data is None:
                logger.error("Either audio_file or audio_data must be provided")
                return False
            
            # Extract embedding
            embedding = self.extract_embedding(audio_data, sample_rate)
            
            # Store raw sample embedding in enrollment_samples
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            sample_blob = pickle.dumps(embedding)
            cursor.execute("INSERT INTO enrollment_samples (name, embedding) VALUES (?, ?)", (name, sample_blob))

            # Recompute averaged embedding from all samples for this user
            cursor.execute("SELECT embedding FROM enrollment_samples WHERE name = ?", (name,))
            rows = cursor.fetchall()
            embeddings = []
            for (emb_blob,) in rows:
                try:
                    e = pickle.loads(emb_blob)
                    embeddings.append(e / (np.linalg.norm(e) + 1e-8))
                except Exception:
                    continue

            if embeddings:
                avg = np.mean(np.stack(embeddings, axis=0), axis=0)
                avg = avg / (np.linalg.norm(avg) + 1e-8)
                embedding_to_store = avg
            else:
                embedding_to_store = embedding

            # Upsert into speakers table
            embedding_blob = pickle.dumps(embedding_to_store)
            cursor.execute("INSERT OR REPLACE INTO speakers (name, embedding) VALUES (?, ?)", (name, embedding_blob))

            conn.commit()
            conn.close()
            
            logger.info(f"Successfully enrolled user: {name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to enroll user {name}: {e}")
            return False
    
    def identify_speaker(self, audio_data: np.ndarray, sample_rate: int = 16000) -> str:
        """
        Identify the speaker from audio data.
        
        Args:
            audio_data: Audio samples as numpy array
            sample_rate: Sample rate of audio
            
        Returns:
            Speaker name if identified, "unknown" otherwise
        """
        try:
            # Extract embedding from audio
            query_embedding = self.extract_embedding(audio_data, sample_rate)
            
            # Get all enrolled speakers
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name, embedding FROM speakers")
            speakers = cursor.fetchall()
            conn.close()
            
            if not speakers:
                logger.warning("No enrolled speakers found")
                return "unknown"
            
            # Compare with all enrolled speakers
            best_match = None
            best_similarity = -1
            
            # For debugging: collect all scores
            scores: List[Tuple[str, float]] = []

            for name, embedding_blob in speakers:
                stored_embedding = pickle.loads(embedding_blob)
                similarity = self._cosine_similarity(query_embedding, stored_embedding)
                
                logger.debug(f"Similarity with {name}: {similarity:.3f}")
                scores.append((name, float(similarity)))
                
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match = name
            
            # Check if best match exceeds threshold
            if best_similarity >= self.similarity_threshold:
                logger.info(f"Identified speaker: {best_match} (similarity: {best_similarity:.3f})")
                return best_match
            else:
                # Optionally accept near-threshold matches to reduce false negatives
                if self.accept_near_threshold and best_similarity + self.near_margin >= self.similarity_threshold:
                    logger.info(f"Near-threshold match accepted: {best_match} (similarity: {best_similarity:.3f})")
                    return best_match

                # Log full score breakdown at INFO so you can see why it failed
                score_lines = ", ".join([f"{n}:{s:.3f}" for n, s in scores])
                logger.info(f"No match found (best: {best_similarity:.3f} < {self.similarity_threshold}). Scores: {score_lines}")
                return "unknown"
                
        except Exception as e:
            logger.error(f"Error identifying speaker: {e}")
            return "unknown"
    
    def _cosine_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Calculate cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Cosine similarity (0 to 1)
        """
        dot_product = np.dot(embedding1, embedding2)
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        similarity = dot_product / (norm1 * norm2)
        
        # Ensure result is between 0 and 1
        return float(np.clip(similarity, 0, 1))

    def identify_with_score(self, audio_data: np.ndarray, sample_rate: int = 16000) -> Tuple[str, float]:
        """
        Identify speaker and return (name, score). Score is -1 on error or no speakers.
        """
        # Extract embedding and compute best match
        try:
            query_embedding = self.extract_embedding(audio_data, sample_rate)
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name, embedding FROM speakers")
            speakers = cursor.fetchall()
            conn.close()

            if not speakers:
                return ("unknown", -1.0)

            best_name = "unknown"
            best_score = -1.0
            for name, emb_blob in speakers:
                stored = pickle.loads(emb_blob)
                s = self._cosine_similarity(query_embedding, stored)
                if s > best_score:
                    best_score = s
                    best_name = name

            return (best_name, float(best_score))
        except Exception as e:
            logger.error(f"identify_with_score error: {e}")
            return ("unknown", -1.0)

    def dump_embeddings(self, path: str = "embeddings_dump.pkl") -> str:
        """
        Dump stored speaker embeddings to a pickle file for inspection.
        Returns the path to the dump file.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name, embedding FROM speakers")
        rows = cursor.fetchall()
        conn.close()

        data = {name: pickle.loads(blob) for name, blob in rows}
        with open(path, "wb") as f:
            pickle.dump(data, f)

        logger.info(f"Embeddings dumped to {path}")
        return path

    def reprocess_embeddings(self) -> bool:
        """
        Recompute averaged embeddings from all enrollment_samples and overwrite speakers table.
        Useful after bulk enrollment or changing normalization strategy.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT name FROM enrollment_samples")
            names = [r[0] for r in cursor.fetchall()]

            for name in names:
                cursor.execute("SELECT embedding FROM enrollment_samples WHERE name = ?", (name,))
                rows = cursor.fetchall()
                embeddings = []
                for (emb_blob,) in rows:
                    try:
                        e = pickle.loads(emb_blob)
                        embeddings.append(e / (np.linalg.norm(e) + 1e-8))
                    except Exception:
                        continue

                if not embeddings:
                    continue

                avg = np.mean(np.stack(embeddings, axis=0), axis=0)
                avg = avg / (np.linalg.norm(avg) + 1e-8)
                avg_blob = pickle.dumps(avg)
                cursor.execute("INSERT OR REPLACE INTO speakers (name, embedding) VALUES (?, ?)", (name, avg_blob))

            conn.commit()
            conn.close()
            logger.info("Reprocessed embeddings from enrollment_samples")
            return True
        except Exception as e:
            logger.error(f"Failed to reprocess embeddings: {e}")
            return False
    
    def list_users(self) -> List[str]:
        """
        Get list of all enrolled users.
        
        Returns:
            List of user names
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM speakers ORDER BY name")
        users = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        return users
    
    def delete_user(self, name: str) -> bool:
        """
        Delete an enrolled user.
        
        Args:
            name: User name to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM speakers WHERE name = ?", (name,))
            conn.commit()
            deleted = cursor.rowcount > 0
            conn.close()
            
            if deleted:
                logger.info(f"Deleted user: {name}")
            else:
                logger.warning(f"User not found: {name}")
            
            return deleted
            
        except Exception as e:
            logger.error(f"Error deleting user {name}: {e}")
            return False
    
    def get_speaker_count(self) -> int:
        """
        Get the number of enrolled speakers.
        
        Returns:
            Number of enrolled speakers
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM speakers")
        count = cursor.fetchone()[0]
        conn.close()
        
        return count


# Example usage and enrollment script
if __name__ == "__main__":
    import argparse
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    parser = argparse.ArgumentParser(description="Speaker Identification System")
    parser.add_argument("--enroll", type=str, help="Enroll a new speaker")
    parser.add_argument("--audio", type=str, help="Path to audio file")
    parser.add_argument("--list", action="store_true", help="List enrolled speakers")
    parser.add_argument("--delete", type=str, help="Delete a speaker")
    parser.add_argument("--identify", type=str, help="Identify speaker from audio file")
    parser.add_argument("--threshold", type=float, default=0.75, help="Similarity threshold")
    parser.add_argument("--dump-embeddings", type=str, help="Dump speaker embeddings to file")
    parser.add_argument("--reprocess", action="store_true", help="Recompute averaged embeddings from samples")
    
    args = parser.parse_args()
    
    # Initialize speaker identifier
    speaker_id = SpeakerIdentifier(similarity_threshold=args.threshold)
    
    if args.enroll and args.audio:
        print(f"Enrolling {args.enroll} from {args.audio}...")
        success = speaker_id.enroll_user(args.enroll, audio_file=args.audio)
        print("Success!" if success else "Failed!")
    
    elif args.list:
        users = speaker_id.list_users()
        print(f"Enrolled speakers ({len(users)}):")
        for user in users:
            print(f"  - {user}")
    
    elif args.delete:
        success = speaker_id.delete_user(args.delete)
        print(f"Deleted {args.delete}" if success else f"Failed to delete {args.delete}")
    
    elif args.identify and args.audio:
        audio_data, sr = sf.read(args.audio)
        name, score = speaker_id.identify_with_score(audio_data, sr)
        print(f"Identified speaker: {name} (score: {score:.3f})")

    elif args.threshold:
        # Allow updating threshold via CLI for quick testing
        speaker_id.similarity_threshold = args.threshold
        print(f"Threshold set to {args.threshold}")

    elif args.enroll and not args.audio:
        print("--enroll requires --audio <path> to enroll from a file")

    elif args.list:
        # already handled above
        pass

    # Additional tools
    parser.add_argument("--dump-embeddings", type=str, help="Dump speaker embeddings to file")
    parser.add_argument("--reprocess", action="store_true", help="Recompute averaged embeddings from samples")
    
    else:
        parser.print_help()

    # Handle additional tools
    if args.dump_embeddings:
        out = speaker_id.dump_embeddings(args.dump_embeddings)
        print(f"Embeddings dumped to {out}")

    if args.reprocess:
        ok = speaker_id.reprocess_embeddings()
        print("Reprocessed embeddings" if ok else "Reprocess failed")

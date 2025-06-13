import logging
import threading
import fcntl
import queue
import atexit

# Import E2B implementation
from .code_task_e2b import run_ai_code_task_e2b

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# For backward compatibility, we'll keep the queue structure for Codex tasks
# but it will use E2B sandboxes instead of Docker containers

# Global Codex execution queue and lock for sequential processing
codex_execution_queue = queue.Queue()
codex_execution_lock = threading.Lock()
codex_worker_thread = None
codex_lock_file = '/tmp/codex_global_lock'

def init_codex_sequential_processor():
    """Initialize the sequential Codex processor"""
    global codex_worker_thread
    
    def codex_worker():
        """Worker thread that processes Codex tasks sequentially"""
        logger.info("🔄 Codex sequential worker thread started")
        
        while True:
            try:
                # Get the next task from the queue (blocks if empty)
                task_data = codex_execution_queue.get(timeout=1.0)
                if task_data is None:  # Poison pill to stop the thread
                    logger.info("🛑 Codex worker thread stopping")
                    break
                    
                task_id, user_id, github_token = task_data
                logger.info(f"🎯 Processing Codex task {task_id} sequentially")
                
                # Acquire file-based lock for additional safety
                try:
                    with open(codex_lock_file, 'w') as lock_file:
                        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
                        logger.info(f"🔒 Global Codex lock acquired for task {task_id}")
                        
                        # Execute the task using E2B
                        run_ai_code_task_e2b(task_id, user_id, github_token)
                            
                        logger.info(f"✅ Codex task {task_id} completed")
                        
                except Exception as e:
                    logger.error(f"❌ Error executing Codex task {task_id}: {e}")
                finally:
                    codex_execution_queue.task_done()
                    
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"❌ Error in Codex worker thread: {e}")
                
    # Start the worker thread if not already running
    with codex_execution_lock:
        if codex_worker_thread is None or not codex_worker_thread.is_alive():
            codex_worker_thread = threading.Thread(target=codex_worker, daemon=True)
            codex_worker_thread.start()
            logger.info("🚀 Codex sequential processor initialized")

def queue_codex_task(task_id, user_id, github_token):
    """Queue a Codex task for sequential execution"""
    init_codex_sequential_processor()
    
    logger.info(f"📋 Queuing Codex task {task_id} for sequential execution")
    codex_execution_queue.put((task_id, user_id, github_token))
    
    # Wait for the task to be processed
    logger.info(f"⏳ Waiting for Codex task {task_id} to be processed...")
    codex_execution_queue.join()

# Cleanup function to stop the worker thread
def cleanup_codex_processor():
    """Clean up the Codex processor on exit"""
    global codex_worker_thread
    if codex_worker_thread and codex_worker_thread.is_alive():
        logger.info("🧹 Shutting down Codex sequential processor")
        codex_execution_queue.put(None)  # Poison pill
        codex_worker_thread.join(timeout=5.0)

atexit.register(cleanup_codex_processor)
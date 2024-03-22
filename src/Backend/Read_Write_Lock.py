import threading


class ReadWriteLock:
    # Constructor to initialize the lock and read count
    def __init__(self):
        self._lock = threading.Lock()  # A lock to protect the read count
        self._read_lock = threading.Lock() # A lock to protect the shared resource during reads
        self._write_lock = threading.Lock()  # A lock to protect the shared resource during writes
        self._read_count = 0  # The number of threads currently holding a read lock

    # Method to acquire a read lock
    def acquire_read(self):
        with self._lock:
         # Increment the read count and acquire the write lock if this is the first reader
            self._read_count += 1
            if self._read_count == 1:
                self._write_lock.acquire()
        self._read_lock.acquire()  # Acquire the read lock

    # Method to release a read lock
    def release_read(self):
        self._read_lock.release() # Release the read lock
        with self._lock:
        # Decrement the read count and release the write lock if this is the last reader
            self._read_count -= 1
            if self._read_count == 0:
                self._write_lock.release()

    # Method to acquire a write lock
    def acquire_write(self):
        self._write_lock.acquire()

    # Method to release a write lock
    def release_write(self):
        self._write_lock.release()

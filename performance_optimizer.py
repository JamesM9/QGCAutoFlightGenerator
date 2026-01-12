#!/usr/bin/env python3
"""
Performance Optimization System
Provides caching, background processing, and resource management
"""

import json
import os
import time
import threading
import queue
from datetime import datetime, timedelta
from collections import OrderedDict
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                              QPushButton, QProgressBar, QTextEdit, QFrame,
                              QDialog, QDialogButtonBox, QSpinBox, QCheckBox,
                              QGroupBox, QSlider, QListWidget, QListWidgetItem)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QThread, QObject, QMutex
from PyQt5.QtGui import QFont, QColor, QPixmap, QPainter

class CacheManager:
    """Manages application caching for improved performance"""
    
    def __init__(self, max_size_mb=500, cleanup_interval=3600):
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.cleanup_interval = cleanup_interval
        self.cache_dir = "cache"
        self.cache_index = OrderedDict()
        self.cache_stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'total_size': 0
        }
        self.mutex = QMutex()
        
        self.setup_cache_directory()
        self.load_cache_index()
        self.start_cleanup_timer()
        
    def setup_cache_directory(self):
        """Setup cache directory"""
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
    
    def load_cache_index(self):
        """Load cache index from file"""
        index_file = os.path.join(self.cache_dir, "cache_index.json")
        try:
            if os.path.exists(index_file):
                with open(index_file, 'r') as f:
                    data = json.load(f)
                    self.cache_index = OrderedDict(data.get('entries', {}))
                    self.cache_stats = data.get('stats', self.cache_stats)
        except Exception as e:
            print(f"Error loading cache index: {e}")
    
    def save_cache_index(self):
        """Save cache index to file"""
        index_file = os.path.join(self.cache_dir, "cache_index.json")
        try:
            data = {
                'entries': dict(self.cache_index),
                'stats': self.cache_stats
            }
            with open(index_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving cache index: {e}")
    
    def start_cleanup_timer(self):
        """Start periodic cache cleanup timer"""
        self.cleanup_timer = QTimer()
        self.cleanup_timer.timeout.connect(self.cleanup_cache)
        self.cleanup_timer.start(self.cleanup_interval * 1000)
    
    def get_cache_key(self, category, identifier):
        """Generate cache key"""
        return f"{category}_{identifier}"
    
    def get(self, category, identifier):
        """Get item from cache"""
        self.mutex.lock()
        try:
            key = self.get_cache_key(category, identifier)
            
            if key in self.cache_index:
                entry = self.cache_index[key]
                
                # Check if entry is expired
                if self.is_entry_expired(entry):
                    self.remove_entry(key)
                    self.cache_stats['misses'] += 1
                    return None
                
                # Move to end (LRU)
                self.cache_index.move_to_end(key)
                
                # Update access time
                entry['last_accessed'] = datetime.now().isoformat()
                
                self.cache_stats['hits'] += 1
                
                # Load data from file
                file_path = os.path.join(self.cache_dir, entry['filename'])
                if os.path.exists(file_path):
                    with open(file_path, 'r') as f:
                        return json.load(f)
                else:
                    self.remove_entry(key)
                    self.cache_stats['misses'] += 1
                    return None
            else:
                self.cache_stats['misses'] += 1
                return None
        finally:
            self.mutex.unlock()
    
    def put(self, category, identifier, data, ttl_seconds=3600):
        """Put item in cache"""
        self.mutex.lock()
        try:
            key = self.get_cache_key(category, identifier)
            
            # Generate filename
            filename = f"{key}_{int(time.time())}.json"
            file_path = os.path.join(self.cache_dir, filename)
            
            # Save data to file
            with open(file_path, 'w') as f:
                json.dump(data, f)
            
            # Calculate file size
            file_size = os.path.getsize(file_path)
            
            # Create cache entry
            entry = {
                'filename': filename,
                'size': file_size,
                'created': datetime.now().isoformat(),
                'last_accessed': datetime.now().isoformat(),
                'ttl': ttl_seconds,
                'category': category
            }
            
            # Remove existing entry if exists
            if key in self.cache_index:
                self.remove_entry(key)
            
            # Add new entry
            self.cache_index[key] = entry
            self.cache_stats['total_size'] += file_size
            
            # Ensure cache size limit
            self.enforce_size_limit()
            
            self.save_cache_index()
            
        finally:
            self.mutex.unlock()
    
    def remove_entry(self, key):
        """Remove cache entry"""
        if key in self.cache_index:
            entry = self.cache_index[key]
            
            # Remove file
            file_path = os.path.join(self.cache_dir, entry['filename'])
            if os.path.exists(file_path):
                os.remove(file_path)
            
            # Update stats
            self.cache_stats['total_size'] -= entry['size']
            self.cache_stats['evictions'] += 1
            
            # Remove from index
            del self.cache_index[key]
    
    def is_entry_expired(self, entry):
        """Check if cache entry is expired"""
        created_time = datetime.fromisoformat(entry['created'])
        ttl = timedelta(seconds=entry['ttl'])
        return datetime.now() - created_time > ttl
    
    def enforce_size_limit(self):
        """Enforce cache size limit using LRU eviction"""
        while self.cache_stats['total_size'] > self.max_size_bytes and self.cache_index:
            # Remove oldest entry (LRU)
            oldest_key = next(iter(self.cache_index))
            self.remove_entry(oldest_key)
    
    def cleanup_cache(self):
        """Clean up expired cache entries"""
        self.mutex.lock()
        try:
            expired_keys = []
            for key, entry in self.cache_index.items():
                if self.is_entry_expired(entry):
                    expired_keys.append(key)
            
            for key in expired_keys:
                self.remove_entry(key)
            
            if expired_keys:
                self.save_cache_index()
                print(f"Cleaned up {len(expired_keys)} expired cache entries")
        finally:
            self.mutex.unlock()
    
    def get_cache_stats(self):
        """Get cache statistics"""
        hit_rate = 0
        if self.cache_stats['hits'] + self.cache_stats['misses'] > 0:
            hit_rate = self.cache_stats['hits'] / (self.cache_stats['hits'] + self.cache_stats['misses'])
        
        return {
            'hits': self.cache_stats['hits'],
            'misses': self.cache_stats['misses'],
            'evictions': self.cache_stats['evictions'],
            'total_size_mb': self.cache_stats['total_size'] / (1024 * 1024),
            'hit_rate': hit_rate,
            'entries': len(self.cache_index)
        }
    
    def clear_cache(self):
        """Clear all cache entries"""
        self.mutex.lock()
        try:
            # Remove all files
            for entry in self.cache_index.values():
                file_path = os.path.join(self.cache_dir, entry['filename'])
                if os.path.exists(file_path):
                    os.remove(file_path)
            
            # Clear index
            self.cache_index.clear()
            self.cache_stats['total_size'] = 0
            
            self.save_cache_index()
        finally:
            self.mutex.unlock()

class BackgroundWorker(QThread):
    """Background worker for long-running tasks"""
    
    progress_updated = pyqtSignal(int, str)  # progress, message
    task_completed = pyqtSignal(object)      # result
    task_failed = pyqtSignal(str)            # error message
    
    def __init__(self, task_func, *args, **kwargs):
        super().__init__()
        self.task_func = task_func
        self.args = args
        self.kwargs = kwargs
        self.cancelled = False
        
    def run(self):
        """Run the background task"""
        try:
            result = self.task_func(*self.args, **self.kwargs)
            if not self.cancelled:
                self.task_completed.emit(result)
        except Exception as e:
            if not self.cancelled:
                self.task_failed.emit(str(e))
    
    def cancel(self):
        """Cancel the task"""
        self.cancelled = True

class BackgroundTaskManager(QObject):
    """Manages background tasks and workers"""
    
    task_started = pyqtSignal(str)      # task_name
    task_completed = pyqtSignal(str)    # task_name
    task_failed = pyqtSignal(str, str)  # task_name, error
    
    def __init__(self, max_workers=3):
        super().__init__()
        self.max_workers = max_workers
        self.active_workers = {}
        self.task_queue = queue.Queue()
        self.worker_semaphore = threading.Semaphore(max_workers)
        
    def submit_task(self, task_name, task_func, *args, **kwargs):
        """Submit a task for background execution"""
        if len(self.active_workers) >= self.max_workers:
            # Queue the task
            self.task_queue.put((task_name, task_func, args, kwargs))
            return False
        
        self.start_task(task_name, task_func, *args, **kwargs)
        return True
    
    def start_task(self, task_name, task_func, *args, **kwargs):
        """Start a background task"""
        worker = BackgroundWorker(task_func, *args, **kwargs)
        worker.task_completed.connect(lambda result: self.on_task_completed(task_name, result))
        worker.task_failed.connect(lambda error: self.on_task_failed(task_name, error))
        
        self.active_workers[task_name] = worker
        worker.start()
        
        self.task_started.emit(task_name)
    
    def on_task_completed(self, task_name, result):
        """Handle task completion"""
        if task_name in self.active_workers:
            worker = self.active_workers[task_name]
            worker.wait()
            del self.active_workers[task_name]
        
        self.task_completed.emit(task_name)
        
        # Process queued tasks
        self.process_queued_tasks()
    
    def on_task_failed(self, task_name, error):
        """Handle task failure"""
        if task_name in self.active_workers:
            worker = self.active_workers[task_name]
            worker.wait()
            del self.active_workers[task_name]
        
        self.task_failed.emit(task_name, error)
        
        # Process queued tasks
        self.process_queued_tasks()
    
    def process_queued_tasks(self):
        """Process queued tasks"""
        while not self.task_queue.empty() and len(self.active_workers) < self.max_workers:
            task_name, task_func, args, kwargs = self.task_queue.get()
            self.start_task(task_name, task_func, *args, **kwargs)
    
    def cancel_task(self, task_name):
        """Cancel a specific task"""
        if task_name in self.active_workers:
            worker = self.active_workers[task_name]
            worker.cancel()
            worker.wait()
            del self.active_workers[task_name]
    
    def cancel_all_tasks(self):
        """Cancel all active tasks"""
        for task_name in list(self.active_workers.keys()):
            self.cancel_task(task_name)
    
    def get_active_tasks(self):
        """Get list of active task names"""
        return list(self.active_workers.keys())
    
    def get_queue_size(self):
        """Get number of queued tasks"""
        return self.task_queue.qsize()

class ResourceMonitor(QObject):
    """Monitors system resources and performance"""
    
    resource_warning = pyqtSignal(str, str)  # resource_type, message
    
    def __init__(self):
        super().__init__()
        self.memory_threshold = 80  # percentage
        self.cpu_threshold = 90     # percentage
        self.disk_threshold = 85    # percentage
        self.monitoring = False
        self.monitor_timer = QTimer()
        self.monitor_timer.timeout.connect(self.check_resources)
        
    def start_monitoring(self, interval_seconds=30):
        """Start resource monitoring"""
        self.monitoring = True
        self.monitor_timer.start(interval_seconds * 1000)
    
    def stop_monitoring(self):
        """Stop resource monitoring"""
        self.monitoring = False
        self.monitor_timer.stop()
    
    def check_resources(self):
        """Check system resources"""
        try:
            # Memory usage (simplified)
            memory_usage = self.get_memory_usage()
            if memory_usage > self.memory_threshold:
                self.resource_warning.emit("memory", f"High memory usage: {memory_usage}%")
            
            # CPU usage (simplified)
            cpu_usage = self.get_cpu_usage()
            if cpu_usage > self.cpu_threshold:
                self.resource_warning.emit("cpu", f"High CPU usage: {cpu_usage}%")
            
            # Disk usage
            disk_usage = self.get_disk_usage()
            if disk_usage > self.disk_threshold:
                self.resource_warning.emit("disk", f"High disk usage: {disk_usage}%")
                
        except Exception as e:
            print(f"Error monitoring resources: {e}")
    
    def get_memory_usage(self):
        """Get memory usage percentage (simplified)"""
        try:
            import psutil
            return psutil.virtual_memory().percent
        except ImportError:
            # Fallback to simplified calculation
            return 50  # Placeholder
    
    def get_cpu_usage(self):
        """Get CPU usage percentage (simplified)"""
        try:
            import psutil
            return psutil.cpu_percent()
        except ImportError:
            # Fallback to simplified calculation
            return 30  # Placeholder
    
    def get_disk_usage(self):
        """Get disk usage percentage"""
        try:
            import psutil
            return psutil.disk_usage('/').percent
        except ImportError:
            # Fallback to simplified calculation
            return 60  # Placeholder

class PerformanceOptimizer(QObject):
    """Main performance optimization manager"""
    
    optimization_completed = pyqtSignal(str)  # optimization_type
    performance_warning = pyqtSignal(str, str)  # warning_type, message
    
    def __init__(self):
        super().__init__()
        self.cache_manager = CacheManager()
        self.task_manager = BackgroundTaskManager()
        self.resource_monitor = ResourceMonitor()
        
        # Connect signals
        self.resource_monitor.resource_warning.connect(self.on_resource_warning)
        self.task_manager.task_failed.connect(self.on_task_failed)
        
        # Start monitoring
        self.resource_monitor.start_monitoring()
    
    def on_resource_warning(self, resource_type, message):
        """Handle resource warnings"""
        self.performance_warning.emit(resource_type, message)
        
        # Take automatic action
        if resource_type == "memory":
            self.optimize_memory()
        elif resource_type == "disk":
            self.cleanup_cache()
    
    def on_task_failed(self, task_name, error):
        """Handle task failures"""
        print(f"Background task failed: {task_name} - {error}")
    
    def optimize_memory(self):
        """Optimize memory usage"""
        # Clear some cache entries
        self.cache_manager.cleanup_cache()
        self.optimization_completed.emit("memory")
    
    def cleanup_cache(self):
        """Clean up cache"""
        self.cache_manager.cleanup_cache()
        self.optimization_completed.emit("cache")
    
    def get_performance_stats(self):
        """Get performance statistics"""
        cache_stats = self.cache_manager.get_cache_stats()
        active_tasks = self.task_manager.get_active_tasks()
        queue_size = self.task_manager.get_queue_size()
        
        return {
            'cache': cache_stats,
            'active_tasks': active_tasks,
            'queued_tasks': queue_size,
            'memory_usage': self.resource_monitor.get_memory_usage(),
            'cpu_usage': self.resource_monitor.get_cpu_usage(),
            'disk_usage': self.resource_monitor.get_disk_usage()
        }
    
    def submit_background_task(self, task_name, task_func, *args, **kwargs):
        """Submit a task for background execution"""
        return self.task_manager.submit_task(task_name, task_func, *args, **kwargs)
    
    def get_cached_data(self, category, identifier):
        """Get data from cache"""
        return self.cache_manager.get(category, identifier)
    
    def cache_data(self, category, identifier, data, ttl_seconds=3600):
        """Cache data"""
        self.cache_manager.put(category, identifier, data, ttl_seconds)

class PerformanceMonitorWidget(QWidget):
    """Widget for monitoring performance metrics"""
    
    def __init__(self, optimizer, parent=None):
        super().__init__(parent)
        self.optimizer = optimizer
        self.setup_ui()
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_metrics)
        self.update_timer.start(5000)  # Update every 5 seconds
        
    def setup_ui(self):
        """Setup the performance monitor UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Title
        title_label = QLabel("Performance Monitor")
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        title_label.setStyleSheet("color: #00d4aa;")
        layout.addWidget(title_label)
        
        # Cache Statistics
        cache_group = QGroupBox("Cache Statistics")
        cache_layout = QVBoxLayout(cache_group)
        
        self.cache_hits_label = QLabel("Cache Hits: 0")
        cache_layout.addWidget(self.cache_hits_label)
        
        self.cache_misses_label = QLabel("Cache Misses: 0")
        cache_layout.addWidget(self.cache_misses_label)
        
        self.cache_hit_rate_label = QLabel("Hit Rate: 0%")
        cache_layout.addWidget(self.cache_hit_rate_label)
        
        self.cache_size_label = QLabel("Cache Size: 0 MB")
        cache_layout.addWidget(self.cache_size_label)
        
        layout.addWidget(cache_group)
        
        # System Resources
        resources_group = QGroupBox("System Resources")
        resources_layout = QVBoxLayout(resources_group)
        
        self.memory_progress = QProgressBar()
        self.memory_progress.setFormat("Memory: %p%")
        resources_layout.addWidget(self.memory_progress)
        
        self.cpu_progress = QProgressBar()
        self.cpu_progress.setFormat("CPU: %p%")
        resources_layout.addWidget(self.cpu_progress)
        
        self.disk_progress = QProgressBar()
        self.disk_progress.setFormat("Disk: %p%")
        resources_layout.addWidget(self.disk_progress)
        
        layout.addWidget(resources_group)
        
        # Background Tasks
        tasks_group = QGroupBox("Background Tasks")
        tasks_layout = QVBoxLayout(tasks_group)
        
        self.active_tasks_label = QLabel("Active Tasks: 0")
        tasks_layout.addWidget(self.active_tasks_label)
        
        self.queued_tasks_label = QLabel("Queued Tasks: 0")
        tasks_layout.addWidget(self.queued_tasks_label)
        
        layout.addWidget(tasks_group)
        
        # Control Buttons
        buttons_layout = QHBoxLayout()
        
        self.optimize_btn = QPushButton("Optimize Memory")
        self.optimize_btn.clicked.connect(self.optimize_memory)
        buttons_layout.addWidget(self.optimize_btn)
        
        self.cleanup_btn = QPushButton("Cleanup Cache")
        self.cleanup_btn.clicked.connect(self.cleanup_cache)
        buttons_layout.addWidget(self.cleanup_btn)
        
        layout.addLayout(buttons_layout)
        
        self.apply_theme()
        
    def apply_theme(self):
        """Apply the dark theme styling"""
        self.setStyleSheet("""
            QWidget {
                background-color: #1a2332;
                color: white;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #2d3748;
                border-radius: 8px;
                margin-top: 1ex;
                padding-top: 15px;
                padding-bottom: 15px;
                padding-left: 15px;
                padding-right: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 8px 0 8px;
                color: #00d4aa;
            }
            QProgressBar {
                border: 2px solid #4a5568;
                border-radius: 5px;
                text-align: center;
                background-color: #2d3748;
            }
            QProgressBar::chunk {
                background-color: #00d4aa;
                border-radius: 3px;
            }
            QPushButton {
                background-color: #2d3748;
                color: white;
                border: 2px solid #4a5568;
                border-radius: 5px;
                padding: 8px 16px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #4a5568;
                border-color: #00d4aa;
            }
            QPushButton:pressed {
                background-color: #00d4aa;
                color: #1a2332;
            }
        """)
        
    def update_metrics(self):
        """Update performance metrics display"""
        stats = self.optimizer.get_performance_stats()
        
        # Update cache statistics
        cache_stats = stats['cache']
        self.cache_hits_label.setText(f"Cache Hits: {cache_stats['hits']}")
        self.cache_misses_label.setText(f"Cache Misses: {cache_stats['misses']}")
        self.cache_hit_rate_label.setText(f"Hit Rate: {cache_stats['hit_rate']:.1%}")
        self.cache_size_label.setText(f"Cache Size: {cache_stats['total_size_mb']:.1f} MB")
        
        # Update system resources
        self.memory_progress.setValue(int(stats['memory_usage']))
        self.cpu_progress.setValue(int(stats['cpu_usage']))
        self.disk_progress.setValue(int(stats['disk_usage']))
        
        # Update task information
        self.active_tasks_label.setText(f"Active Tasks: {len(stats['active_tasks'])}")
        self.queued_tasks_label.setText(f"Queued Tasks: {stats['queued_tasks']}")
        
        # Update progress bar colors based on usage
        self.update_progress_colors()
    
    def update_progress_colors(self):
        """Update progress bar colors based on usage levels"""
        # Memory progress
        memory_value = self.memory_progress.value()
        if memory_value > 80:
            self.memory_progress.setStyleSheet("QProgressBar::chunk { background-color: #ef4444; }")
        elif memory_value > 60:
            self.memory_progress.setStyleSheet("QProgressBar::chunk { background-color: #f59e0b; }")
        else:
            self.memory_progress.setStyleSheet("QProgressBar::chunk { background-color: #00d4aa; }")
        
        # CPU progress
        cpu_value = self.cpu_progress.value()
        if cpu_value > 80:
            self.cpu_progress.setStyleSheet("QProgressBar::chunk { background-color: #ef4444; }")
        elif cpu_value > 60:
            self.cpu_progress.setStyleSheet("QProgressBar::chunk { background-color: #f59e0b; }")
        else:
            self.cpu_progress.setStyleSheet("QProgressBar::chunk { background-color: #00d4aa; }")
        
        # Disk progress
        disk_value = self.disk_progress.value()
        if disk_value > 80:
            self.disk_progress.setStyleSheet("QProgressBar::chunk { background-color: #ef4444; }")
        elif disk_value > 60:
            self.disk_progress.setStyleSheet("QProgressBar::chunk { background-color: #f59e0b; }")
        else:
            self.disk_progress.setStyleSheet("QProgressBar::chunk { background-color: #00d4aa; }")
    
    def optimize_memory(self):
        """Trigger memory optimization"""
        self.optimizer.optimize_memory()
    
    def cleanup_cache(self):
        """Trigger cache cleanup"""
        self.optimizer.cleanup_cache()

# Global performance optimizer instance
performance_optimizer = PerformanceOptimizer()

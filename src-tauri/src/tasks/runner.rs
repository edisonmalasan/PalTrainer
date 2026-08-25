//! Long-running background task runner with progress reporting and cooperative cancellation.

use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::{Arc, Mutex};

#[derive(Clone, Copy, Debug, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "lowercase")]
pub enum TaskStatus {
    Queued,
    Running,
    Completed,
    Failed,
    Cancelled,
}

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct TaskProgress {
    pub task_id: String,
    pub status: TaskStatus,
    pub current: usize,
    pub total: usize,
    pub percentage: f32,
    pub message: String,
}

#[derive(Clone, Default)]
pub struct CancellationToken {
    cancelled: Arc<AtomicBool>,
}

impl CancellationToken {
    pub fn new() -> Self {
        Self {
            cancelled: Arc::new(AtomicBool::new(false)),
        }
    }

    pub fn cancel(&self) {
        self.cancelled.store(true, Ordering::SeqCst);
    }

    pub fn is_cancelled(&self) -> bool {
        self.cancelled.load(Ordering::SeqCst)
    }
}

pub struct TaskTracker {
    tasks: Mutex<HashMap<String, (TaskProgress, CancellationToken)>>,
}

impl Default for TaskTracker {
    fn default() -> Self {
        Self::new()
    }
}

impl TaskTracker {
    pub fn new() -> Self {
        Self {
            tasks: Mutex::new(HashMap::new()),
        }
    }

    pub fn register_task(
        &self,
        task_id: impl Into<String>,
        total: usize,
        message: impl Into<String>,
    ) -> (String, CancellationToken) {
        let id = task_id.into();
        let token = CancellationToken::new();
        let progress = TaskProgress {
            task_id: id.clone(),
            status: TaskStatus::Running,
            current: 0,
            total,
            percentage: 0.0,
            message: message.into(),
        };

        if let Ok(mut lock) = self.tasks.lock() {
            lock.insert(id.clone(), (progress, token.clone()));
        }

        (id, token)
    }

    pub fn update_progress(&self, task_id: &str, current: usize, message: Option<&str>) {
        if let Ok(mut lock) = self.tasks.lock() {
            if let Some((progress, _)) = lock.get_mut(task_id) {
                progress.current = current;
                if progress.total > 0 {
                    progress.percentage =
                        ((current as f32 / progress.total as f32) * 100.0).min(100.0);
                }
                if let Some(msg) = message {
                    progress.message = msg.to_string();
                }
            }
        }
    }

    pub fn complete_task(&self, task_id: &str, message: Option<&str>) {
        if let Ok(mut lock) = self.tasks.lock() {
            if let Some((progress, _)) = lock.get_mut(task_id) {
                progress.status = TaskStatus::Completed;
                progress.current = progress.total;
                progress.percentage = 100.0;
                if let Some(msg) = message {
                    progress.message = msg.to_string();
                }
            }
        }
    }

    pub fn fail_task(&self, task_id: &str, error: &str) {
        if let Ok(mut lock) = self.tasks.lock() {
            if let Some((progress, _)) = lock.get_mut(task_id) {
                progress.status = TaskStatus::Failed;
                progress.message = error.to_string();
            }
        }
    }

    pub fn cancel_task(&self, task_id: &str) -> bool {
        if let Ok(mut lock) = self.tasks.lock() {
            if let Some((progress, token)) = lock.get_mut(task_id) {
                token.cancel();
                progress.status = TaskStatus::Cancelled;
                progress.message = "Task cancelled by user".to_string();
                return true;
            }
        }
        false
    }

    pub fn get_progress(&self, task_id: &str) -> Option<TaskProgress> {
        self.tasks.lock().ok()?.get(task_id).map(|(p, _)| p.clone())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_task_tracker_lifecycle() {
        let tracker = TaskTracker::new();
        let (task_id, token) = tracker.register_task("task_1", 100, "Starting work");

        assert!(!token.is_cancelled());
        tracker.update_progress(&task_id, 50, Some("Halfway"));

        let progress = tracker.get_progress(&task_id).unwrap();
        assert_eq!(progress.current, 50);
        assert_eq!(progress.percentage, 50.0);
        assert_eq!(progress.message, "Halfway");

        tracker.complete_task(&task_id, Some("Done"));
        let completed = tracker.get_progress(&task_id).unwrap();
        assert_eq!(completed.status, TaskStatus::Completed);
    }

    #[test]
    fn test_task_cancellation() {
        let tracker = TaskTracker::new();
        let (task_id, token) = tracker.register_task("cancel_test", 100, "In progress");

        assert!(tracker.cancel_task(&task_id));
        assert!(token.is_cancelled());

        let progress = tracker.get_progress(&task_id).unwrap();
        assert_eq!(progress.status, TaskStatus::Cancelled);
    }

    #[test]
    fn test_task_failure() {
        let tracker = TaskTracker::new();
        let (task_id, _) = tracker.register_task("fail_test", 50, "Working");

        tracker.fail_task(&task_id, "Out of memory");
        let progress = tracker.get_progress(&task_id).unwrap();
        assert_eq!(progress.status, TaskStatus::Failed);
        assert_eq!(progress.message, "Out of memory");
    }

    #[test]
    fn test_non_existent_task_operations() {
        let tracker = TaskTracker::new();
        assert!(!tracker.cancel_task("does_not_exist"));
        assert!(tracker.get_progress("does_not_exist").is_none());
    }

    #[test]
    fn test_progress_clamped_at_100() {
        let tracker = TaskTracker::new();
        let (task_id, _) = tracker.register_task("clamp_test", 100, "Progressing");

        tracker.update_progress(&task_id, 150, None);
        let progress = tracker.get_progress(&task_id).unwrap();
        assert_eq!(progress.percentage, 100.0);
    }
}

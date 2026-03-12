# Use advanced AI for task understanding and execution
        from core.advanced_task_executor import advanced_executor
        
        # First, try to understand the task using AI
        task_understanding = advanced_executor.understand_task(description)
        
        if task_understanding["confidence"] < 0.3:
            # Low confidence, fall back to simple execution
            return self._execute_simple_task(task_id, description, max_steps)
        
        # High confidence, use advanced multi-step execution
        execution_plan = task_understanding["execution_plan"]
        execution_result = advanced_executor.execute_plan(execution_plan)
        
        # Generate response based on execution results
        if execution_result["success"]:
            response = f"Task completed successfully! {execution_result['summary']}"
            
            self._emit_execution_event(
                "step_progress",
                f"Step {step_num}: {action}",
                task_id=task_id,
                step_number=step_num,
                action=action,
                details=details,
                success=step.get("success", False),
                message=step.get("message", ""),
            )
            
            # Add delay between steps for better UX
            time.sleep(0.2)
        
        # Final completion event
        self._emit_execution_event(
            "task_complete",
            f"Advanced task execution completed: {execution_result['summary']}",
            task_id=task_id,
            result=execution_result
        )
        
    except Exception as e:
        error_msg = f"Advanced task execution failed: {e}"
        print(f"[FunctionExecutor] {error_msg}")
        
        self._emit_execution_event(
            "task_error",
            error_msg,
            task_id=task_id,
            error=str(e)
        )
    
    # Return the result
    return {
        "success": execution_result["success"],
        "message": response,
        "execution_result": execution_result
    }

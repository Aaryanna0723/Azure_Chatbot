# Global state
class GlobalState:
    def __init__(self):
        self.question_list = []
        self.response_list = []
        self.current_index = 0
        self.summary_context = ""
        self.chat_state = "waiting_for_issue"  # States: waiting_for_issue, asking_questions, completed
        self.chat_history=[]

# Create a global instance
global_state = GlobalState()

from enum import Enum, auto


class SessionState(Enum):
    ANONYMOUS = auto()
    AWAITING_2FA = auto()
    AWAITING_ONBOARDING = auto()
    AUTHENTICATED = auto()

class SessionProtocol:
    _TRANSITIONS = {
        SessionState.ANONYMOUS: [SessionState.AWAITING_2FA, SessionState.AWAITING_ONBOARDING],
        SessionState.AWAITING_2FA: [SessionState.AUTHENTICATED, SessionState.AWAITING_ONBOARDING, SessionState.ANONYMOUS],
        SessionState.AWAITING_ONBOARDING: [SessionState.AUTHENTICATED],
        SessionState.AUTHENTICATED: [SessionState.ANONYMOUS],
    }

    def __init__(self, request):
        self.request = request
        state_name = request.session.get('protocol_state', SessionState.ANONYMOUS.name)
        try:
            self.current_state = SessionState[state_name]
        except KeyError:
            self.current_state = SessionState.ANONYMOUS

    def transition_to(self, next_state: SessionState):
        if self.current_state == next_state:
            return

        if next_state in self._TRANSITIONS.get(self.current_state, []):
            self.request.session['protocol_state'] = next_state.name
            self.current_state = next_state
        else:
            raise PermissionError(f"Protocol Violation: {self.current_state} -> {next_state}")

    def is_at(self, state: SessionState):
        return self.current_state == state

from datetime import datetime
from typing import Dict, List


# sys monitor

class SystemMonitor:
    """
    Runtime monitoring system.

    Responsibilities:
    - monitor workflow health
    - track system events
    - observe execution lifecycle
    - centralize monitoring logs
    """

    def __init__(self):

        self.events = []


    # log event 

    def log_event(
        self,
        level: str,
        component: str,
        message: str
    ) -> None:
        """
        Store monitoring event.
        """

        self.events.append({

            "timestamp": (
                datetime.utcnow()
                .isoformat()
            ),

            "level": level,

            "component": component,

            "message": message
        })


    # info event 

    def info(
        self,
        component: str,
        message: str
    ) -> None:
        """
        Record info-level event.
        """

        self.log_event(
            level="INFO",
            component=component,
            message=message
        )


    # warning events

    def warning(
        self,
        component: str,
        message: str
    ) -> None:
        """
        Record warning-level event.
        """

        self.log_event(
            level="WARNING",
            component=component,
            message=message
        )


    # error events 

    def error(
        self,
        component: str,
        message: str
    ) -> None:
        """
        Record error-level event.
        """

        self.log_event(
            level="ERROR",
            component=component,
            message=message
        )


    # get events 

    def get_events(
        self,
        limit: int = 50
    ) -> List[Dict]:
        """
        Retrieve recent monitoring events.
        """

        return self.events[-limit:]


    # sys health 

    def system_health(self) -> Dict:
        """
        Basic workflow health report.
        """

        error_count = len([

            event

            for event in self.events

            if event["level"] == "ERROR"
        ])

        warning_count = len([

            event

            for event in self.events

            if event["level"] == "WARNING"
        ])

        return {

            "status": (
                "healthy"
                if error_count == 0
                else "degraded"
            ),

            "total_events": len(
                self.events
            ),

            "errors": error_count,

            "warnings": warning_count
        }


# global monitor

system_monitor = SystemMonitor()
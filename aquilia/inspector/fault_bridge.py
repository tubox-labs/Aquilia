from aquilia.faults.core import FaultContext

from .trace import ExceptionNode, Lane, SpanStatus, current_trace


def get_fault_listener(config):
    def listener(ctx: FaultContext) -> None:
        trace = current_trace()
        if trace is None:
            return

        fingerprint = ctx.fingerprint()

        # Safely extract stack frames
        frames = []
        tb = ctx.cause.__traceback__ if ctx.cause else None
        while tb:
            frame = tb.tb_frame
            code_obj = frame.f_code
            frames.append(
                {
                    "filename": code_obj.co_filename,
                    "lineno": tb.tb_lineno,
                    "name": code_obj.co_name,
                }
            )
            tb = tb.tb_next

        node = ExceptionNode(
            exception_type=type(ctx.cause).__name__ if ctx.cause else "Fault",
            message=ctx.fault.message,
            fault_code=ctx.fault.code,
            fault_domain=str(ctx.fault.domain.value),
            fingerprint=fingerprint,
            stack_frames=frames,
        )
        trace.exception = node

        # Also add a span to show the fault occurring in the timeline
        trace.add_span(
            Lane.EXCEPTION,
            f"Fault: {ctx.fault.code}",
            start_offset_ms=trace.duration_ms,  # current offset
            duration_ms=0.0,  # point event
            status=SpanStatus.ERROR,
            detail={"message": ctx.fault.message},
        )

    return listener

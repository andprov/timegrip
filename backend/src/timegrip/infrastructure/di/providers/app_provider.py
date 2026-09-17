from dishka import Provider, Scope, provide

from timegrip.application.auth.add_user import AddUserInteractor
from timegrip.application.auth.login import AuthUserInteractor
from timegrip.application.auth.refresh_token_manager import (
    RefreshTokenManager,
)
from timegrip.application.cleanup.cleanup_old_emails import (
    CleanupOldEmailsInteractor,
)
from timegrip.application.cleanup.cleanup_refresh_tokens import (
    CleanupRefreshTokensInteractor,
)
from timegrip.application.cleanup.cleanup_unconfirmed_users import (
    CleanupUnconfirmedUsersInteractor,
)
from timegrip.application.outbox.send_pending_emails import (
    SendPendingEmailsInteractor,
)
from timegrip.application.password_reset.forgot_password import (
    ForgotPasswordInteractor,
)
from timegrip.application.password_reset.password_reset_code_manager import (
    PasswordResetCodeManager,
)
from timegrip.application.password_reset.reset_password import (
    ResetPasswordInteractor,
)
from timegrip.application.project.add_project import (
    AddProjectInteractor,
)
from timegrip.application.project.delete_project import (
    DeleteProjectInteractor,
)
from timegrip.application.project.get_all_user_projects import (
    GetAllUserProjectsInteractor,
)
from timegrip.application.project.get_project import (
    GetProjectByIdInteractor,
)
from timegrip.application.project.update_project import (
    UpdateProjectInteractor,
)
from timegrip.application.timer.add_manual_timer import (
    AddManualTimerInteractor,
)
from timegrip.application.timer.bulk_delete_timer import (
    BulkDeleteTimerInteractor,
)
from timegrip.application.timer.delete_timer import (
    DeleteTimerInteractor,
)
from timegrip.application.timer.get_all_user_timers import (
    GetAllUserTimersInteractor,
)
from timegrip.application.timer.get_running_timer import (
    GetRunningTimerInteractor,
)
from timegrip.application.timer.get_timer import GetTimerByIdInteractor
from timegrip.application.timer.start_timer import StartTimerInteractor
from timegrip.application.timer.stop_timer import StopTimerInteractor
from timegrip.application.timer.update_timer import UpdateTimerInteractor
from timegrip.application.user.activate_user import (
    ActivateUserInteractor,
)
from timegrip.application.user.delete_user import DeleteUserInteractor
from timegrip.application.user.get_user import GetUserByIdInteractor
from timegrip.application.user.update_email import UpdateEmailInteractor
from timegrip.application.user.update_locale import UpdateLocaleInteractor
from timegrip.application.user.update_password import (
    UpdatePasswordInteractor,
)
from timegrip.application.user.update_time_format import (
    UpdateTimeFormatInteractor,
)
from timegrip.application.user_activation.activation_code_manager import (
    ActivationCodeManager,
)
from timegrip.application.user_activation.get_resend_cooldown import (
    GetResendCooldownInteractor,
)
from timegrip.application.user_activation.resend_activation_code import (
    ResendActivationCodeInteractor,
)


class AppProvider(Provider):
    activation_code_manager = provide(
        source=ActivationCodeManager,
        scope=Scope.REQUEST,
    )
    add_user = provide(
        source=AddUserInteractor,
        scope=Scope.REQUEST,
    )
    auth_user = provide(
        source=AuthUserInteractor,
        scope=Scope.REQUEST,
    )
    get_user_by_id = provide(
        source=GetUserByIdInteractor,
        scope=Scope.REQUEST,
    )
    update_password = provide(
        source=UpdatePasswordInteractor,
        scope=Scope.REQUEST,
    )
    update_email = provide(
        source=UpdateEmailInteractor,
        scope=Scope.REQUEST,
    )
    update_time_format = provide(
        source=UpdateTimeFormatInteractor,
        scope=Scope.REQUEST,
    )
    update_locale = provide(
        source=UpdateLocaleInteractor,
        scope=Scope.REQUEST,
    )
    delete_user = provide(
        source=DeleteUserInteractor,
        scope=Scope.REQUEST,
    )
    activate_user = provide(
        source=ActivateUserInteractor,
        scope=Scope.REQUEST,
    )
    resend_activation_code = provide(
        source=ResendActivationCodeInteractor,
        scope=Scope.REQUEST,
    )
    get_resend_cooldown = provide(
        source=GetResendCooldownInteractor,
        scope=Scope.REQUEST,
    )
    password_reset_code_manager = provide(
        source=PasswordResetCodeManager,
        scope=Scope.REQUEST,
    )
    refresh_token_manager = provide(
        source=RefreshTokenManager,
        scope=Scope.REQUEST,
    )
    forgot_password = provide(
        source=ForgotPasswordInteractor,
        scope=Scope.REQUEST,
    )
    reset_password = provide(
        source=ResetPasswordInteractor,
        scope=Scope.REQUEST,
    )
    send_pending_emails = provide(
        source=SendPendingEmailsInteractor,
        scope=Scope.REQUEST,
    )
    cleanup_unconfirmed_users = provide(
        source=CleanupUnconfirmedUsersInteractor,
        scope=Scope.REQUEST,
    )
    cleanup_old_emails = provide(
        source=CleanupOldEmailsInteractor,
        scope=Scope.REQUEST,
    )
    cleanup_refresh_tokens = provide(
        source=CleanupRefreshTokensInteractor,
        scope=Scope.REQUEST,
    )
    add_project = provide(
        source=AddProjectInteractor,
        scope=Scope.REQUEST,
    )
    get_all_projects = provide(
        source=GetAllUserProjectsInteractor,
        scope=Scope.REQUEST,
    )
    get_project_by_id = provide(
        source=GetProjectByIdInteractor,
        scope=Scope.REQUEST,
    )
    update_project = provide(
        source=UpdateProjectInteractor,
        scope=Scope.REQUEST,
    )
    delete_project = provide(
        source=DeleteProjectInteractor,
        scope=Scope.REQUEST,
    )
    start_timer = provide(
        source=StartTimerInteractor,
        scope=Scope.REQUEST,
    )
    add_manual_timer = provide(
        source=AddManualTimerInteractor,
        scope=Scope.REQUEST,
    )
    stop_timer = provide(
        source=StopTimerInteractor,
        scope=Scope.REQUEST,
    )
    update_timer = provide(
        source=UpdateTimerInteractor,
        scope=Scope.REQUEST,
    )
    get_running_timer = provide(
        source=GetRunningTimerInteractor,
        scope=Scope.REQUEST,
    )
    get_all_user_timers = provide(
        source=GetAllUserTimersInteractor,
        scope=Scope.REQUEST,
    )
    get_timer_by_id = provide(
        source=GetTimerByIdInteractor,
        scope=Scope.REQUEST,
    )
    delete_timer = provide(
        source=DeleteTimerInteractor,
        scope=Scope.REQUEST,
    )
    bulk_delete_timer = provide(
        source=BulkDeleteTimerInteractor,
        scope=Scope.REQUEST,
    )

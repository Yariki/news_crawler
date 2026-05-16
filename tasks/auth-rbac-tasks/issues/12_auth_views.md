# Login, Register, and Password Reset views

## Goal
Public-facing auth UI flows.

## Tasks
- [ ] `LoginView.vue` at `/login`
  - [ ] Email + password fields with validation
  - [ ] Submit calls `authStore.login()`
  - [ ] On success: redirect to `returnUrl` or `/`
  - [ ] Error states (invalid credentials, inactive account, rate limited)
- [ ] `RegisterView.vue` at `/register` (if self-registration allowed)
  - [ ] Email, username, password, password-confirm
  - [ ] Same validation rules as backend
  - [ ] On success: redirect to login (or auto-login)
- [ ] `ForgotPasswordView.vue` at `/forgot-password`
  - [ ] Email input → POST `/auth/forgot-password`
  - [ ] Show neutral "If the email exists, we sent a link" message (don't reveal account existence)
- [ ] `ResetPasswordView.vue` at `/reset-password/:token`
  - [ ] New password + confirm
  - [ ] POST `/auth/reset-password` with token
- [ ] Shared `AuthLayout.vue` (centered card, logo)
- [ ] Form validation via VeeValidate or Vuelidate

## Acceptance criteria
- All flows work end-to-end against the backend
- Validation messages are clear and accessible (a11y)
- Loading and error states handled

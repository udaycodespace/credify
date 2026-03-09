import logging
import os
from flask_mail import Mail, Message
from flask import render_template_string

logger = logging.getLogger(__name__)

SUPPORT_EMAIL = "udayworksoffical@gmail.com"

NUKE_REPORT_TEMPLATE = """
<!DOCTYPE html>
<html>
<body style="margin:0;padding:0;background:#fef2f2;font-family:'Segoe UI',Arial,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#fef2f2;padding:40px 0;">
  <tr><td align="center">
    <table width="600" cellpadding="0" cellspacing="0" style="background:#ffffff;border:1px solid #fee2e2;border-radius:12px;overflow:hidden;box-shadow:0 10px 15px -3px rgba(0,0,0,0.1);">
      <tr><td style="background:#991b1b;padding:24px;text-align:center;color:#ffffff;">
        <h2 style="margin:0;font-size:20px;letter-spacing:2px;text-transform:uppercase;">Critical System Action</h2>
        <p style="margin:4px 0 0 0;opacity:0.8;font-size:12px;">SYSTEM RESET COMPLETE</p>
      </td></tr>
      <tr><td style="padding:40px 32px;color:#1e293b;">
        <p style="margin:0 0 20px 0;font-size:16px;font-weight:700;color:#991b1b;">FULL SYSTEM PURGE EXECUTED</p>
        <p style="margin:0 0 24px 0;font-size:14px;line-height:1.6;">A complete system reset has been successfully authorized and executed. The platform has been reverted to its genesis state.</p>
        
        <table width="100%" style="background:#f8fafc;border-radius:8px;padding:20px;margin-bottom:28px;">
          <tr><td>
            <p style="margin:0 0 12px 0;font-size:11px;font-weight:700;color:#64748b;text-transform:uppercase;letter-spacing:1px;">Cleanup Summary</p>
            <ul style="margin:0;padding:0 0 0 20px;font-size:13px;color:#334155;line-height:1.8;">
              <li>{{ stats.credentials }} Credentials destroyed</li>
              <li>{{ stats.students }} Student accounts wiped</li>
              <li>{{ stats.tickets }} Support tickets purged</li>
              <li>{{ stats.messages }} Communication logs cleared</li>
              <li>{{ stats.blocks }} Blockchain blocks reset</li>
            </ul>
          </td></tr>
        </table>
        
        <div style="background:#fff7ed;border-left:4px solid #f97316;padding:16px;margin-bottom:28px;">
          <p style="margin:0;font-size:13px;color:#9a3412;line-height:1.6;">
            <strong>Audit Manifest Attached:</strong> A detailed PDF manifest of all deleted data is attached to this email. 
            <br><br>
            <strong>PDF Password:</strong> Use the 6-digit authorization code used to execute the reset.
          </p>
        </div>
        
        <p style="margin:0;font-size:12px;color:#94a3b8;border-top:1px solid #f1f5f9;padding-top:24px;">
          This is an automated security record. No further action is required unless this was unauthorized.
        </p>
      </td></tr>
    </table>
  </td></tr>
</table>
</body>
</html>
"""

SECURITY_OTP_TEMPLATE = """
<!DOCTYPE html>
<html>
<body style="margin:0;padding:0;background:#f8fafc;font-family:'Segoe UI',Arial,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f8fafc;padding:40px 0;">
  <tr><td align="center">
    <table width="500" cellpadding="0" cellspacing="0" style="background:#ffffff;border:1px solid #e2e8f0;border-radius:12px;overflow:hidden;box-shadow:0 4px 6px rgba(0,0,0,0.05);">
      <tr><td style="background:#0f172a;padding:24px;text-align:center;">
        <h2 style="margin:0;color:#38bdf8;font-size:18px;letter-spacing:1px;text-transform:uppercase;">Credify Security Alert</h2>
      </td></tr>
      <tr><td style="padding:40px 32px;color:#334155;">
        <p style="margin:0 0 16px 0;font-size:16px;font-weight:600;">Administrative Login Initiated</p>
        <p style="margin:0 0 24px 0;font-size:14px;line-height:1.6;">Hello {{ full_name }},<br><br>A login attempt was made for your <strong>Credify Administrative</strong> account. To verify your identity, please enter the following 6-digit code:</p>
        
        <div style="background:#f1f5f9;border-radius:8px;padding:24px;text-align:center;margin-bottom:24px;">
          <p style="margin:0 0 8px 0;font-size:12px;color:#64748b;text-transform:uppercase;letter-spacing:1px;font-weight:700;">Security Code</p>
          <p style="margin:0;font-size:32px;font-weight:800;color:#0f172a;letter-spacing:4px;">{{ otp }}</p>
        </div>
        
        <p style="margin:0 0 24px 0;font-size:13px;color:#64748b;line-height:1.6;">This code will expire in 10 minutes. If you did <strong>NOT</strong> initiate this login, please change your password immediately to secure your account.</p>
        
        <div style="border-top:1px solid #f1f5f9;padding-top:24px;">
          <p style="margin:0;font-size:12px;color:#94a3b8;">Securely yours,<br><strong>Credify DevOps Team</strong></p>
        </div>
      </td></tr>
    </table>
  </td></tr>
</table>
</body>
</html>
"""

# ─────────────────────────────────────────────────────────────────
# EMAIL 1 — Credential Verification
# ─────────────────────────────────────────────────────────────────
ONBOARDING_TEMPLATE = """
<!DOCTYPE html>
<html>
<body style="margin:0;padding:0;background:#f4f6f9;font-family:'Segoe UI',Tahoma,Geneva,Verdana,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f6f9;padding:32px 0;">
  <tr><td align="center">
    <table width="600" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:8px;overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,0.08);">

      <!-- Header -->
      <tr>
        <td style="background:#0f2044;padding:28px 32px;text-align:center;">
          <p style="margin:0;color:#a0b4cc;font-size:12px;letter-spacing:2px;text-transform:uppercase;">Credify Academic Credential System</p>
          <h1 style="margin:6px 0 0 0;color:#ffffff;font-size:22px;font-weight:700;">G. Pulla Reddy Engineering College (Autonomous)</h1>
        </td>
      </tr>

      <!-- Body -->
      <tr>
        <td style="padding:36px 40px;color:#1e293b;">
          <p style="margin:0 0 16px 0;font-size:15px;">Dear {{ full_name }},</p>
          <p style="margin:0 0 16px 0;font-size:15px;line-height:1.7;color:#334155;">
            The Academic Records Office of <strong>G. Pulla Reddy Engineering College</strong> has issued a digital academic credential for you through the <strong>Credify Credential System</strong>.
          </p>
          <p style="margin:0 0 28px 0;font-size:15px;line-height:1.7;color:#334155;">
            Before this credential is activated, we require you to confirm that the email address and academic details are correct.
          </p>

          <!-- Credential Summary -->
          <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;padding:24px;margin-bottom:28px;">
            <p style="margin:0 0 16px 0;font-size:11px;font-weight:700;color:#64748b;letter-spacing:1.5px;text-transform:uppercase;">Credential Summary</p>
            <table width="100%" cellpadding="0" cellspacing="0">
              <tr>
                <td style="padding:10px 0;border-bottom:1px solid #e2e8f0;">
                  <p style="margin:0;font-size:12px;color:#64748b;font-weight:600;text-transform:uppercase;letter-spacing:0.5px;">Program</p>
                  <p style="margin:4px 0 0 0;font-size:15px;font-weight:600;color:#0f172a;">{{ degree }}</p>
                </td>
              </tr>
              <tr>
                <td style="padding:10px 0;border-bottom:1px solid #e2e8f0;">
                  <p style="margin:0;font-size:12px;color:#64748b;font-weight:600;text-transform:uppercase;letter-spacing:0.5px;">Graduation Year</p>
                  <p style="margin:4px 0 0 0;font-size:15px;font-weight:600;color:#0f172a;">{{ year }}</p>
                </td>
              </tr>
              <tr>
                <td style="padding:10px 0;border-bottom:1px solid #e2e8f0;">
                  <p style="margin:0;font-size:12px;color:#64748b;font-weight:600;text-transform:uppercase;letter-spacing:0.5px;">GPA</p>
                  <p style="margin:4px 0 0 0;font-size:15px;font-weight:600;color:#0f172a;">{{ gpa }} / 10.00</p>
                </td>
              </tr>
              <tr>
                <td style="padding:10px 0;">
                  <p style="margin:0;font-size:12px;color:#64748b;font-weight:600;text-transform:uppercase;letter-spacing:0.5px;">Credential Status</p>
                  <p style="margin:4px 0 0 0;font-size:15px;font-weight:600;color:#d97706;">Pending Student Verification</p>
                </td>
              </tr>
            </table>
          </div>

          <!-- Verification Required -->
          <p style="margin:0 0 8px 0;font-size:16px;font-weight:700;color:#0f172a;">Verification Required</p>
          <p style="margin:0 0 24px 0;font-size:15px;color:#334155;line-height:1.7;">
            Please confirm that this credential belongs to you and that the details above are accurate.
          </p>
          <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:12px;">
            <tr>
              <td align="center">
                <a href="{{ yes_link }}" style="display:inline-block;background:#166534;color:#ffffff;padding:14px 36px;border-radius:6px;text-decoration:none;font-size:15px;font-weight:700;letter-spacing:0.3px;">Verify My Credential</a>
              </td>
            </tr>
          </table>
          <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:32px;">
            <tr>
              <td align="center">
                <a href="{{ no_link }}" style="display:inline-block;background:#ffffff;color:#dc2626;padding:13px 36px;border-radius:6px;text-decoration:none;font-size:14px;font-weight:600;border:2px solid #dc2626;">Report an Issue</a>
              </td>
            </tr>
          </table>
          <p style="margin:0 0 8px 0;font-size:14px;color:#64748b;line-height:1.7;">
            Our Academic Records team will review the request and take appropriate action.
          </p>

          <!-- Why section -->
          <div style="background:#fffbeb;border:1px solid #fde68a;border-radius:6px;padding:16px;margin-top:28px;">
            <p style="margin:0 0 6px 0;font-size:13px;font-weight:700;color:#92400e;">Why this step is required</p>
            <p style="margin:0;font-size:13px;color:#78350f;line-height:1.6;">
              This verification ensures that the credential is securely linked to the correct student identity before it becomes accessible.
            </p>
          </div>
        </td>
      </tr>

      <!-- Footer -->
      <tr>
        <td style="background:#f1f5f9;padding:20px 40px;border-top:1px solid #e2e8f0;">
          <p style="margin:0;font-size:12px;color:#64748b;line-height:1.8;">
            <strong style="color:#334155;">Credify Digital Credential Platform</strong><br>
            Academic Records Office<br>
            G. Pulla Reddy Engineering College (Autonomous)<br>
            Support: <a href="mailto:{{ support_email }}" style="color:#2563eb;text-decoration:none;">{{ support_email }}</a>
          </p>
        </td>
      </tr>

    </table>
  </td></tr>
</table>
</body>
</html>
"""

# ─────────────────────────────────────────────────────────────────
# EMAIL 2 — Activate Your Student Account
# ─────────────────────────────────────────────────────────────────
CREDENTIAL_READY_TEMPLATE = """
<!DOCTYPE html>
<html>
<body style="margin:0;padding:0;background:#f4f6f9;font-family:'Segoe UI',Tahoma,Geneva,Verdana,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f6f9;padding:32px 0;">
  <tr><td align="center">
    <table width="600" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:8px;overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,0.08);">

      <!-- Header -->
      <tr>
        <td style="background:#0f2044;padding:28px 32px;text-align:center;">
          <p style="margin:0;color:#a0b4cc;font-size:12px;letter-spacing:2px;text-transform:uppercase;">Credify Digital Credential Platform</p>
          <h1 style="margin:6px 0 0 0;color:#ffffff;font-size:22px;font-weight:700;">G. Pulla Reddy Engineering College (Autonomous)</h1>
        </td>
      </tr>

      <!-- Body -->
      <tr>
        <td style="padding:36px 40px;color:#1e293b;">
          <p style="margin:0 0 16px 0;font-size:15px;">Dear {{ full_name }},</p>
          <p style="margin:0 0 8px 0;font-size:15px;color:#334155;line-height:1.7;">
            Thank you for verifying your academic credential.
          </p>
          <p style="margin:0 0 28px 0;font-size:15px;color:#334155;line-height:1.7;">
            Your student account is now ready to be activated.<br>
            Please complete the final setup to access your <strong>Credify Student Portal</strong>.
          </p>

          <!-- Credential Info -->
          <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;padding:24px;margin-bottom:28px;">
            <p style="margin:0 0 16px 0;font-size:11px;font-weight:700;color:#64748b;letter-spacing:1.5px;text-transform:uppercase;">Credential Information</p>
            <table width="100%" cellpadding="0" cellspacing="0">
              <tr>
                <td style="padding:10px 0;border-bottom:1px solid #e2e8f0;">
                  <p style="margin:0;font-size:12px;color:#64748b;font-weight:600;text-transform:uppercase;letter-spacing:0.5px;">Program</p>
                  <p style="margin:4px 0 0 0;font-size:15px;font-weight:600;color:#0f172a;">{{ degree }}</p>
                </td>
              </tr>
              <tr>
                <td style="padding:10px 0;border-bottom:1px solid #e2e8f0;">
                  <p style="margin:0;font-size:12px;color:#64748b;font-weight:600;text-transform:uppercase;letter-spacing:0.5px;">Graduation Year</p>
                  <p style="margin:4px 0 0 0;font-size:15px;font-weight:600;color:#0f172a;">{{ year }}</p>
                </td>
              </tr>
              <tr>
                <td style="padding:10px 0;border-bottom:1px solid #e2e8f0;">
                  <p style="margin:0;font-size:12px;color:#64748b;font-weight:600;text-transform:uppercase;letter-spacing:0.5px;">Student Roll Number</p>
                  <p style="margin:4px 0 0 0;font-size:15px;font-weight:600;color:#0f172a;">{{ student_id }}</p>
                </td>
              </tr>
              <tr>
                <td style="padding:10px 0;">
                  <p style="margin:0;font-size:12px;color:#64748b;font-weight:600;text-transform:uppercase;letter-spacing:0.5px;">Credential ID</p>
                  <p style="margin:4px 0 0 0;font-size:13px;font-weight:600;color:#0f172a;font-family:'Courier New',monospace;">{{ credential_id }}</p>
                </td>
              </tr>
            </table>
          </div>

          <!-- Next Step -->
          <p style="margin:0 0 8px 0;font-size:16px;font-weight:700;color:#0f172a;">Next Step</p>
          <p style="margin:0 0 20px 0;font-size:15px;color:#334155;line-height:1.7;">
            Click the button below to create your username and password.
          </p>
          <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:28px;">
            <tr>
              <td align="center">
                <a href="{{ setup_link }}" style="display:inline-block;background:#0f2044;color:#ffffff;padding:15px 40px;border-radius:6px;text-decoration:none;font-size:15px;font-weight:700;">Set Up My Account</a>
              </td>
            </tr>
          </table>

          <!-- During setup -->
          <div style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:6px;padding:16px;margin-bottom:24px;">
            <p style="margin:0 0 8px 0;font-size:13px;font-weight:700;color:#166534;">During Setup You Will</p>
            <p style="margin:0;font-size:13px;color:#166534;line-height:1.8;">
              • Create your username<br>
              • Set a secure password
            </p>
          </div>
          <p style="margin:0 0 20px 0;font-size:14px;color:#334155;line-height:1.7;">
            Once completed, you will be able to log in and access your digital academic transcript.
          </p>

          <!-- Important -->
          <div style="background:#fffbeb;border:1px solid #fde68a;border-radius:6px;padding:16px;">
            <p style="margin:0 0 8px 0;font-size:13px;font-weight:700;color:#92400e;">Important</p>
            <p style="margin:0;font-size:13px;color:#78350f;line-height:1.8;">
              Please keep your Roll Number (<strong>{{ student_id }}</strong>) saved for future reference.<br>
              It may be required for credential verification or account recovery.<br><br>
              For security reasons, this setup link will expire in <strong>1 hour</strong>.<br><br>
              If you did not complete the verification step earlier, please contact the Academic Records Office.
            </p>
          </div>
        </td>
      </tr>

      <!-- Footer -->
      <tr>
        <td style="background:#f1f5f9;padding:20px 40px;border-top:1px solid #e2e8f0;">
          <p style="margin:0;font-size:12px;color:#64748b;line-height:1.8;">
            <strong style="color:#334155;">Credify Digital Credential Platform</strong><br>
            Academic Records Office<br>
            G. Pulla Reddy Engineering College (Autonomous)<br>
            Support: <a href="mailto:{{ support_email }}" style="color:#2563eb;text-decoration:none;">{{ support_email }}</a>
          </p>
        </td>
      </tr>

    </table>
  </td></tr>
</table>
</body>
</html>
"""

# ─────────────────────────────────────────────────────────────────
# EMAIL 3 — Reset Your Account Access
# ─────────────────────────────────────────────────────────────────
RESET_PASSWORD_TEMPLATE = """
<!DOCTYPE html>
<html>
<body style="margin:0;padding:0;background:#f4f6f9;font-family:'Segoe UI',Tahoma,Geneva,Verdana,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f6f9;padding:32px 0;">
  <tr><td align="center">
    <table width="600" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:8px;overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,0.08);">

      <!-- Header -->
      <tr>
        <td style="background:#0f2044;padding:28px 32px;text-align:center;">
          <p style="margin:0;color:#a0b4cc;font-size:12px;letter-spacing:2px;text-transform:uppercase;">Credify Digital Credential Platform</p>
          <h1 style="margin:6px 0 0 0;color:#ffffff;font-size:22px;font-weight:700;">G. Pulla Reddy Engineering College (Autonomous)</h1>
        </td>
      </tr>

      <!-- Body -->
      <tr>
        <td style="padding:36px 40px;color:#1e293b;">
          <p style="margin:0 0 16px 0;font-size:15px;">Dear {{ full_name }},</p>
          <p style="margin:0 0 28px 0;font-size:15px;color:#334155;line-height:1.7;">
            We received a request to reset the login credentials for your <strong>Credify Student Account</strong>.
          </p>
          <p style="margin:0 0 20px 0;font-size:15px;color:#334155;">
            If you made this request, please click the button below to create a new password and regain access to your account.
          </p>

          <!-- CTA -->
          <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:32px;">
            <tr>
              <td align="center">
                <p style="margin:0 0 12px 0;font-size:14px;font-weight:700;color:#64748b;letter-spacing:0.5px;text-transform:uppercase;">Reset Your Access</p>
                <a href="{{ reset_link }}" style="display:inline-block;background:#0f2044;color:#ffffff;padding:15px 40px;border-radius:6px;text-decoration:none;font-size:15px;font-weight:700;">Reset My Password</a>
              </td>
            </tr>
          </table>

          <!-- Account Info -->
          <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;padding:24px;margin-bottom:28px;">
            <p style="margin:0 0 16px 0;font-size:11px;font-weight:700;color:#64748b;letter-spacing:1.5px;text-transform:uppercase;">Account Information</p>
            <table width="100%" cellpadding="0" cellspacing="0">
              <tr>
                <td style="padding:10px 0;border-bottom:1px solid #e2e8f0;">
                  <p style="margin:0;font-size:12px;color:#64748b;font-weight:600;text-transform:uppercase;letter-spacing:0.5px;">Student Name</p>
                  <p style="margin:4px 0 0 0;font-size:15px;font-weight:600;color:#0f172a;">{{ full_name }}</p>
                </td>
              </tr>
              <tr>
                <td style="padding:10px 0;border-bottom:1px solid #e2e8f0;">
                  <p style="margin:0;font-size:12px;color:#64748b;font-weight:600;text-transform:uppercase;letter-spacing:0.5px;">Roll Number</p>
                  <p style="margin:4px 0 0 0;font-size:15px;font-weight:600;color:#0f172a;">{{ student_id }}</p>
                </td>
              </tr>
              <tr>
                <td style="padding:10px 0;">
                  <p style="margin:0;font-size:12px;color:#64748b;font-weight:600;text-transform:uppercase;letter-spacing:0.5px;">Program</p>
                  <p style="margin:4px 0 0 0;font-size:15px;font-weight:600;color:#0f172a;">{{ program }}</p>
                </td>
              </tr>
            </table>
          </div>

          <p style="margin:0 0 20px 0;font-size:14px;color:#334155;line-height:1.7;">
            After resetting your password, you will be able to log in to the Credify Student Portal and access your digital academic credential.
          </p>

          <!-- Security Notice -->
          <div style="background:#fef2f2;border:1px solid #fecaca;border-radius:6px;padding:16px;">
            <p style="margin:0 0 8px 0;font-size:13px;font-weight:700;color:#991b1b;">Important Security Notice</p>
            <p style="margin:0;font-size:13px;color:#7f1d1d;line-height:1.8;">
              If you did not request this password reset, please ignore this email.<br>
              Your account will remain secure and no changes will be made.<br><br>
              For additional security, this reset link will expire in <strong>30 minutes</strong>.
            </p>
          </div>
        </td>
      </tr>

      <!-- Footer -->
      <tr>
        <td style="background:#f1f5f9;padding:20px 40px;border-top:1px solid #e2e8f0;">
          <p style="margin:0;font-size:12px;color:#64748b;line-height:1.8;">
            <strong style="color:#334155;">Credify Digital Credential Platform</strong><br>
            Academic Records Office<br>
            G. Pulla Reddy Engineering College (Autonomous)<br>
            Support: <a href="mailto:{{ support_email }}" style="color:#2563eb;text-decoration:none;">{{ support_email }}</a>
          </p>
        </td>
      </tr>

    </table>
  </td></tr>
</table>
</body>
</html>
"""

# ─────────────────────────────────────────────────────────────────
# Revocation Template (kept minimal, unchanged by user)
# ─────────────────────────────────────────────────────────────────
REVOCATION_TEMPLATE = """
<!DOCTYPE html>
<html>
<body style="margin:0;padding:0;background:#f4f6f9;font-family:'Segoe UI',sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="padding:32px 0;background:#f4f6f9;">
  <tr><td align="center">
    <table width="600" cellpadding="0" cellspacing="0" style="background:#fff;border-radius:8px;overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,0.08);">
      <tr><td style="background:#dc2626;padding:24px 32px;text-align:center;color:#fff;">
        <h2 style="margin:0;font-size:20px;">CREDENTIAL REVOCATION NOTICE</h2>
        <p style="margin:6px 0 0 0;opacity:0.9;font-size:13px;">Credify Academic Records Office</p>
      </td></tr>
      <tr><td style="padding:32px 40px;color:#1e293b;">
        <p>Your credential for <strong>{{ degree }}</strong> has been <strong style="color:#dc2626;">REVOKED</strong> on the Credify Blockchain Network.</p>
        <p><strong>Reason:</strong> {{ reason }}</p>
        <p>This credential is no longer valid for third-party verification. If you believe this is an error, please open a support ticket immediately.</p>
      </td></tr>
      <tr><td style="background:#f1f5f9;padding:16px 40px;border-top:1px solid #e2e8f0;">
        <p style="margin:0;font-size:12px;color:#64748b;">Credify Digital Credential Platform — Academic Records Office — GPREC (Autonomous)</p>
      </td></tr>
    </table>
  </td></tr>
</table>
</body>
</html>
"""


class CredifyMailer:
    def __init__(self, app=None):
        self.mail = Mail(app) if app else None

    def init_app(self, app):
        self.mail = Mail(app)

    def send_email(self, to_email, subject, body, html_body=None, attachment=None):
        """Generic email sender for custom security messages with optional attachment
        attachment: dict with {name, content_type, data}
        """
        if not self.mail:
            logger.error("Mail system not initialized")
            return False

        msg = Message(
            subject=subject,
            recipients=[to_email],
            body=body,
            sender=("Credify Security", os.environ.get('MAIL_USERNAME')),
        )
        if html_body:
            msg.html = html_body

        if attachment:
            msg.attach(
                attachment.get('name', 'file.pdf'),
                attachment.get('content_type', 'application/pdf'),
                attachment.get('data')
            )

        try:
            self.mail.send(msg)
            logger.info(f"Custom email '{subject}' sent to {to_email}")
            return True
        except Exception as e:
            logger.error(f"Failed to send custom email: {e}")
            return False

    # ── EMAIL 1 ──────────────────────────────────────────────────
    def send_onboarding_mail(self, to_email, full_name, token, degree, gpa, year):
        """Email 1: Credential Verification — Yes/No confirmation"""
        if not self.mail:
            logger.error("Mail system not initialized")
            return False

        base_url = os.environ.get('APP_URL', 'http://localhost:5000')
        yes_link = f"{base_url}/activate/verify?token={token}&action=confirm"
        no_link  = f"{base_url}/activate/verify?token={token}&action=reject"

        html = render_template_string(
            ONBOARDING_TEMPLATE,
            full_name=full_name,
            yes_link=yes_link,
            no_link=no_link,
            degree=degree,
            gpa=gpa,
            year=year,
            support_email=SUPPORT_EMAIL,
        )

        msg = Message(
            subject="Action Required — Verify Your Academic Credential",
            recipients=[to_email],
            html=html,
            sender=("GPREC Academic Records", os.environ.get('MAIL_USERNAME')),
        )
        try:
            self.mail.send(msg)
            logger.info(f"Onboarding mail sent to {to_email}")
            return True
        except Exception as e:
            logger.error(f"Failed to send onboarding mail: {e}")
            return False

    # ── EMAIL 2 ──────────────────────────────────────────────────
    def send_setup_mail(self, to_email, full_name, degree, credential_id, token, student_id="", year=""):
        """Email 2: Activate Your Student Account"""
        if not self.mail:
            logger.error("Mail system not initialized")
            return False

        base_url = os.environ.get('APP_URL', 'http://localhost:5000')
        setup_link = f"{base_url}/activate/setup?token={token}"

        html = render_template_string(
            CREDENTIAL_READY_TEMPLATE,
            full_name=full_name,
            degree=degree,
            credential_id=credential_id,
            setup_link=setup_link,
            student_id=student_id,
            year=year,
            support_email=SUPPORT_EMAIL,
        )

        msg = Message(
            subject="Activate Your Credify Account",
            recipients=[to_email],
            html=html,
            sender=("GPREC Academic Records", os.environ.get('MAIL_USERNAME')),
        )
        try:
            self.mail.send(msg)
            logger.info(f"Setup mail sent to {to_email}")
            return True
        except Exception as e:
            logger.error(f"Failed to send setup mail: {e}")
            return False

    # ── EMAIL 3 ──────────────────────────────────────────────────
    def send_reset_password_mail(self, to_email, full_name, student_id, program, token):
        """Email 3: Reset Your Account Access"""
        if not self.mail:
            return False

        base_url = os.environ.get('APP_URL', 'http://localhost:5000')
        reset_link = f"{base_url}/reset-password/{token}"

        html = render_template_string(
            RESET_PASSWORD_TEMPLATE,
            full_name=full_name,
            student_id=student_id,
            program=program,
            reset_link=reset_link,
            support_email=SUPPORT_EMAIL,
        )

        msg = Message(
            subject="Reset Your Credify Account Password",
            recipients=[to_email],
            html=html,
            sender=("GPREC Academic Records", os.environ.get('MAIL_USERNAME')),
        )
        try:
            self.mail.send(msg)
            return True
        except Exception as e:
            logger.error(f"Failed to send reset mail: {e}")
            return False

    # ── Revocation ────────────────────────────────────────────────
    def send_revocation_mail(self, to_email, degree, reason):
        """Revocation notice"""
        if not self.mail:
            return False

        html = render_template_string(REVOCATION_TEMPLATE, degree=degree, reason=reason)
        msg = Message(
            subject="NOTICE: Your Academic Credential Has Been Revoked",
            recipients=[to_email],
            html=html,
            sender=("GPREC Academic Records", os.environ.get('MAIL_USERNAME')),
        )
        try:
            self.mail.send(msg)
            return True
        except Exception as e:
            logger.error(f"Failed to send revocation mail: {e}")
            return False

    def send_security_otp(self, to_email, full_name, otp):
        """Send 6-digit MFA/Security OTP with premium HTML template"""
        if not self.mail:
            return False
            
        html = render_template_string(SECURITY_OTP_TEMPLATE, full_name=full_name, otp=otp)
        msg = Message(
            subject="🛡️ Security Code: Administrative Login",
            recipients=[to_email],
            html=html,
            sender=("Credify Security", os.environ.get('MAIL_USERNAME')),
        )
        try:
            self.mail.send(msg)
            return True
        except Exception as e:
            logger.error(f"Failed to send security OTP: {e}")
            return False

    def send_nuke_report(self, to_email, stats, pdf_data):
        """Final report after System Nuke with attached PDF"""
        if not self.mail:
            return False
            
        html = render_template_string(NUKE_REPORT_TEMPLATE, stats=stats)
        msg = Message(
            subject="🚨 CRITICAL: System Reset Confirmation & Audit Report",
            recipients=[to_email],
            html=html,
            sender=("Credify System", os.environ.get('MAIL_USERNAME')),
        )
        msg.attach("Credify_Wipeout_Audit.pdf", "application/pdf", pdf_data)
        
        try:
            self.mail.send(msg)
            return True
        except Exception as e:
            logger.error(f"Failed to send nuke report: {e}")
            return False

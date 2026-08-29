from app.extensions import db
from app.models import User, Device, KnowledgeArticle


def seed_if_empty():
    if User.query.first():
        return  # already seeded

    admin = User(username="admin", email="admin@company.com", full_name="Alex IT-Admin",
                 department="IT Operations", role="admin")
    admin.set_password("Admin@12345")

    employee = User(username="jsmith", email="jsmith@company.com", full_name="Jamie Smith",
                     department="Sales", role="employee")
    employee.set_password("Employee@123")

    db.session.add_all([admin, employee])
    db.session.commit()

    devices = [
        Device(owner_id=employee.id, device_name="Jamie's ThinkPad X1", device_type="laptop",
               os_name="Windows 11", ip_address="10.0.4.22", status="online"),
        Device(owner_id=employee.id, device_name="Jamie's iPhone 14", device_type="mobile",
               os_name="iOS 18", ip_address="10.0.4.55", status="online"),
    ]
    db.session.add_all(devices)

    articles = [
        KnowledgeArticle(
            title="VPN client fails to connect",
            category="network",
            keywords="vpn, connect, network, tunnel, timeout",
            content="If the VPN client fails to connect, it is most often caused by an expired "
                    "authentication token, a stale client cache, or a local network firewall block.",
            steps="Sign out and back into the VPN client\nClear the VPN client cache\n"
                  "Confirm the corporate firewall allows UDP 500/4500\nRestart the network adapter",
        ),
        KnowledgeArticle(
            title="Wi-Fi keeps disconnecting",
            category="network",
            keywords="wifi, wireless, disconnect, drop, signal",
            content="Intermittent Wi-Fi drops are usually caused by driver issues or channel congestion "
                    "on the 2.4GHz band.",
            steps="Forget and rejoin the Wi-Fi network\nUpdate the wireless adapter driver\n"
                  "Switch to the 5GHz band if available",
        ),
        KnowledgeArticle(
            title="Laptop won't power on",
            category="hardware",
            keywords="laptop, power, boot, dead, battery, charge",
            content="A laptop that won't power on is typically a battery, charger, or power-button fault.",
            steps="Try a different charger/outlet\nHold power button for 15s to hard reset\n"
                  "Remove and reseat the battery if removable\nCheck for charging LED activity",
        ),
        KnowledgeArticle(
            title="Printer not responding",
            category="hardware",
            keywords="printer, print, offline, queue",
            content="Printers going offline is commonly a driver, spooler, or network queue issue.",
            steps="Restart the print spooler service\nRemove and re-add the printer\n"
                  "Check the printer's IP is still reachable",
        ),
        KnowledgeArticle(
            title="Application crashes on launch",
            category="software",
            keywords="crash, app, software, freeze, error, install",
            content="Application crashes on launch are commonly resolved by clearing cache or reinstalling.",
            steps="Restart the app\nClear application cache/temp files\nUpdate to latest version\n"
                  "Reinstall the application",
        ),
        KnowledgeArticle(
            title="Software update stuck",
            category="software",
            keywords="update, stuck, install, patch, progress",
            content="Updates that hang are usually caused by a corrupted download or insufficient disk space.",
            steps="Cancel and restart the update\nFree up at least 5GB of disk space\n"
                  "Run the update as administrator",
        ),
        KnowledgeArticle(
            title="Account locked after failed logins",
            category="account",
            keywords="password, locked, account, login, access, mfa",
            content="Accounts auto-lock after 5 failed login attempts for 30 minutes, or can be reset via "
                    "the self-service portal.",
            steps="Wait 30 minutes for automatic unlock\nUse the self-service password reset portal\n"
                  "Contact IT if MFA device was also lost",
        ),
        KnowledgeArticle(
            title="Forgot password / MFA reset",
            category="account",
            keywords="forgot, password, reset, mfa, 2fa, authenticator",
            content="Password and MFA resets are self-service via the identity portal, verified by "
                    "manager approval for MFA device changes.",
            steps="Go to the self-service identity portal\nVerify identity via backup email/phone\n"
                  "Set a new password meeting complexity rules",
        ),
    ]
    db.session.add_all(articles)
    db.session.commit()

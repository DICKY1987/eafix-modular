#!/usr/bin/env python3
"""
Installation Script for CLI Multi-Rapid GUI Terminal
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
import argparse


class Installer:
    """GUI Terminal installer"""

    def __init__(self):
        self.install_root = Path.home() / ".gui_terminal"
        self.config_dir = self.install_root / "config"
        self.plugins_dir = self.install_root / "plugins"
        self.logs_dir = self.install_root / "logs"

    def check_requirements(self):
        """Check system requirements"""
        print("Checking system requirements...")

        # Check Python version
        if sys.version_info < (3, 8):
            print("❌ Python 3.8 or higher is required")
            return False

        # Check PyQt6 availability
        try:
            import PyQt6
            print("✅ PyQt6 found")
        except ImportError:
            print("❌ PyQt6 not found. Install with: pip install PyQt6")
            return False

        # Check platform-specific requirements
        if sys.platform == 'win32':
            try:
                import winpty
                print("✅ winpty found")
            except ImportError:
                print("❌ winpty not found. Install with: pip install pywinpty")
                return False
        else:
            try:
                import ptyprocess
                print("✅ ptyprocess found")
            except ImportError:
                print("❌ ptyprocess not found. Install with: pip install ptyprocess")
                return False

        print("✅ All requirements satisfied")
        return True

    def create_directories(self):
        """Create necessary directories"""
        print("Creating directories...")

        directories = [
            self.install_root,
            self.config_dir,
            self.plugins_dir,
            self.logs_dir
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            print(f"✅ Created: {directory}")

    def copy_config_files(self):
        """Copy default configuration files"""
        print("Installing configuration files...")

        config_source = Path(__file__).parent.parent / "config"

        config_files = [
            "default_config.yaml",
            "security_policies.yaml"
        ]

        for config_file in config_files:
            source = config_source / config_file
            dest = self.config_dir / config_file

            if source.exists():
                if not dest.exists():
                    shutil.copy2(source, dest)
                    print(f"✅ Installed: {config_file}")
                else:
                    print(f"⚠️  Skipped (exists): {config_file}")
            else:
                print(f"❌ Missing source: {config_file}")

    def create_desktop_entry(self):
        """Create desktop entry (Linux/macOS)"""
        if sys.platform == 'win32':
            return

        desktop_dir = Path.home() / ".local/share/applications"
        desktop_dir.mkdir(parents=True, exist_ok=True)

        desktop_entry = desktop_dir / "gui-terminal.desktop"

        content = f"""[Desktop Entry]
Name=CLI Multi-Rapid GUI Terminal
Comment=Enterprise-grade GUI terminal
Exec=gui-terminal
Icon=terminal
Terminal=false
Type=Application
Categories=System;TerminalEmulator;
Keywords=terminal;shell;command;
"""

        with open(desktop_entry, 'w') as f:
            f.write(content)

        os.chmod(desktop_entry, 0o755)
        print(f"✅ Created desktop entry: {desktop_entry}")

    def create_startup_script(self):
        """Create startup script"""
        if sys.platform == 'win32':
            script_path = self.install_root / "gui-terminal.bat"
            content = f"""@echo off
python -m gui_terminal.main %*
"""
        else:
            script_path = self.install_root / "gui-terminal.sh"
            content = f"""#!/bin/bash
python -m gui_terminal.main "$@"
"""

        with open(script_path, 'w') as f:
            f.write(content)

        if not sys.platform == 'win32':
            os.chmod(script_path, 0o755)

        print(f"✅ Created startup script: {script_path}")

    def install_systemd_service(self):
        """Install systemd service (Linux only)"""
        if sys.platform != 'linux':
            return

        service_dir = Path.home() / ".config/systemd/user"
        service_dir.mkdir(parents=True, exist_ok=True)

        service_file = service_dir / "gui-terminal.service"

        content = f"""[Unit]
Description=CLI Multi-Rapid GUI Terminal
After=graphical-session.target

[Service]
Type=simple
ExecStart=gui-terminal
Restart=on-failure
Environment=DISPLAY=:0

[Install]
WantedBy=default.target
"""

        with open(service_file, 'w') as f:
            f.write(content)

        print(f"✅ Created systemd service: {service_file}")
        print("   Enable with: systemctl --user enable gui-terminal.service")

    def setup_shell_integration(self):
        """Setup shell integration"""
        print("Setting up shell integration...")

        shell_configs = {
            '.bashrc': 'alias gt="gui-terminal"',
            '.zshrc': 'alias gt="gui-terminal"',
            '.fishrc': 'alias gt gui-terminal'
        }

        for config_file, alias_line in shell_configs.items():
            config_path = Path.home() / config_file

            if config_path.exists():
                with open(config_path, 'r') as f:
                    content = f.read()

                if 'gui-terminal' not in content:
                    with open(config_path, 'a') as f:
                        f.write(f'\n# CLI Multi-Rapid GUI Terminal\n{alias_line}\n')
                    print(f"✅ Added alias to: {config_file}")
                else:
                    print(f"⚠️  Alias exists in: {config_file}")

    def run_post_install_checks(self):
        """Run post-installation checks"""
        print("\nRunning post-installation checks...")

        # Check if gui-terminal command is available
        try:
            result = subprocess.run(['gui-terminal', '--help'],
                                 capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print("✅ gui-terminal command available")
            else:
                print("❌ gui-terminal command failed")
                return False
        except (subprocess.TimeoutExpired, FileNotFoundError):
            print("❌ gui-terminal command not found")
            return False

        # Check configuration files
        required_configs = [
            self.config_dir / "default_config.yaml",
            self.config_dir / "security_policies.yaml"
        ]

        for config_file in required_configs:
            if config_file.exists():
                print(f"✅ Config file: {config_file.name}")
            else:
                print(f"❌ Missing config: {config_file.name}")
                return False

        print("✅ Post-installation checks passed")
        return True

    def install(self, skip_checks=False):
        """Run complete installation"""
        print("🚀 CLI Multi-Rapid GUI Terminal Installer")
        print("=" * 50)

        if not skip_checks and not self.check_requirements():
            print("\n❌ Installation failed: Requirements not met")
            return False

        try:
            self.create_directories()
            self.copy_config_files()
            self.create_startup_script()
            self.create_desktop_entry()
            self.install_systemd_service()
            self.setup_shell_integration()

            if not skip_checks:
                if not self.run_post_install_checks():
                    print("\n⚠️  Installation completed with warnings")
                    return False

            print("\n✅ Installation completed successfully!")
            print(f"📁 Installation directory: {self.install_root}")
            print("🎉 You can now run: gui-terminal")

            return True

        except Exception as e:
            print(f"\n❌ Installation failed: {e}")
            return False

    def uninstall(self):
        """Uninstall GUI Terminal"""
        print("🗑️  Uninstalling CLI Multi-Rapid GUI Terminal...")

        if self.install_root.exists():
            shutil.rmtree(self.install_root)
            print(f"✅ Removed: {self.install_root}")

        # Remove desktop entry
        desktop_entry = Path.home() / ".local/share/applications/gui-terminal.desktop"
        if desktop_entry.exists():
            desktop_entry.unlink()
            print(f"✅ Removed desktop entry")

        # Remove systemd service
        service_file = Path.home() / ".config/systemd/user/gui-terminal.service"
        if service_file.exists():
            service_file.unlink()
            print(f"✅ Removed systemd service")

        print("✅ Uninstallation completed")


def main():
    """Main installation script"""
    parser = argparse.ArgumentParser(description="GUI Terminal Installer")
    parser.add_argument('--uninstall', action='store_true',
                       help='Uninstall GUI Terminal')
    parser.add_argument('--skip-checks', action='store_true',
                       help='Skip requirement checks')

    args = parser.parse_args()

    installer = Installer()

    if args.uninstall:
        installer.uninstall()
    else:
        success = installer.install(skip_checks=args.skip_checks)
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
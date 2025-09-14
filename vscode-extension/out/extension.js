"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.deactivate = exports.activate = void 0;
const vscode = require("vscode");
let webSocketClient;
function activate(context) {
    console.log('CLI Multi-Rapid extension is now active!');
    // Register commands
    const commands = [
        vscode.commands.registerCommand('cliMultiRapid.openCockpit', openCockpit),
        vscode.commands.registerCommand('cliMultiRapid.startWorkflow', startWorkflow),
    ];
    commands.forEach(cmd => context.subscriptions.push(cmd));
    // Status bar item
    const statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 100);
    statusBarItem.text = "$(gear) CLI Multi-Rapid";
    statusBarItem.command = 'cliMultiRapid.openCockpit';
    statusBarItem.tooltip = 'Open CLI Multi-Rapid Workflow Cockpit';
    statusBarItem.show();
    context.subscriptions.push(statusBarItem);
}
exports.activate = activate;
async function openCockpit() {
    try {
        vscode.window.showInformationMessage('Opening CLI Multi-Rapid Workflow Cockpit...');
    }
    catch (error) {
        vscode.window.showErrorMessage(`Failed to open cockpit: ${error}`);
    }
}
async function startWorkflow() {
    try {
        const description = await vscode.window.showInputBox({
            prompt: 'Describe the workflow task',
            placeHolder: 'e.g., Refactor this function to use async/await'
        });
        if (!description) {
            return;
        }
        vscode.window.showInformationMessage(`Workflow started: ${description}`);
    }
    catch (error) {
        vscode.window.showErrorMessage(`Failed to start workflow: ${error}`);
    }
}
function deactivate() {
    if (webSocketClient) {
        // webSocketClient.disconnect();
    }
}
exports.deactivate = deactivate;
//# sourceMappingURL=extension.js.map
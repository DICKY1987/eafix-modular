// githubSave.ts — VS Code extension helper to save files to GitHub via Octokit
import { Octokit } from "@octokit/rest";
import * as vscode from "vscode";

export async function saveToGithub(params: {
  owner: string;
  repo: string;
  path: string;
  content: string; // raw text; we'll base64 encode
  message: string;
  branch: string;
  token?: string;
}) {
  const secrets = vscode?.secretStorage ?? (vscode as any).secrets;
  const token = params.token || (await secrets.get("agentic.github.token"));
  if (!token) {
    throw new Error("No GitHub token. Set agenticDev.githubToken or store in Secret Storage (agentic.github.token).");
  }
  const octokit = new Octokit({ auth: token });

  // get existing sha if file present
  let sha: string | undefined;
  try {
    const cur: any = await octokit.repos.getContent({
      owner: params.owner,
      repo: params.repo,
      path: params.path,
      ref: params.branch
    });
    if (cur && cur.data && !Array.isArray(cur.data) && cur.data.sha) {
      sha = cur.data.sha as string;
    }
  } catch (e: any) {
    if (e.status !== 404) throw e;
  }

  const content_b64 = Buffer.from(params.content, "utf8").toString("base64");

  await octokit.repos.createOrUpdateFileContents({
    owner: params.owner,
    repo: params.repo,
    path: params.path,
    message: params.message,
    content: content_b64,
    branch: params.branch,
    sha
  });
}

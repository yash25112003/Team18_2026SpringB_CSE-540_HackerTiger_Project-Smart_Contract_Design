import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { useToast } from "@/hooks/use-toast";
import blockchainApi from "@/services/blockchainApi";

interface Deployment {
  id: string;
  url: string;
  blockId: string;
  repoUrl: string;
  createdAt: string;
  status: "active" | "updating" | "deleted";
}

export default function DeploymentManager() {
  const [deployments, setDeployments] = useState<Deployment[]>([]);
  const [updatingId, setUpdatingId] = useState<string | null>(null);
  const [newRepoUrl, setNewRepoUrl] = useState("");
  const { toast } = useToast();

  useEffect(() => {
    loadDeployments();
  }, []);

  const mapHistoryToDeployment = (item: any): Deployment | null => {
    if (!item || !item.repo_url || !(item.deployment_id || item.id)) {
      return null;
    }

    return {
      id: item.deployment_id || item.id,
      url: item.deployment_url || `http://127.0.0.1:9000/${item.deployment_id || item.id}/`,
      blockId: item.full_hash,
      repoUrl: item.display_repo_url || item.repo_url,
      createdAt: item.created_at,
      status: item.is_active ? "active" : "deleted",
    };
  };

  const loadDeployments = async () => {
    try {
      const historyResult = await blockchainApi.getDeploymentHistory();
      if (!historyResult.success) {
        throw new Error(historyResult.error || "Unable to load deployment history");
      }

      const backendDeployments = historyResult.history
        .map(mapHistoryToDeployment)
        .filter((item): item is Deployment => item !== null)
        .sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime());
      setDeployments(backendDeployments);
    } catch (error) {
      console.error('Failed to load deployments:', error);
      setDeployments([]);
    }
  };

  const handleUpdateRepo = (id: string) => {
    const deployment = deployments.find(d => d.id === id);
    if (deployment) {
      setUpdatingId(id);
      setNewRepoUrl(deployment.repoUrl);
    }
  };

  const saveRepoUpdate = async (id: string) => {
    if (!newRepoUrl.includes('github.com')) {
      toast({
        title: "Invalid repository URL",
        description: "Please enter a valid GitHub repository URL.",
        variant: "destructive",
      });
      return;
    }

    // Set status to updating
    const updatingDeployments = deployments.map(d => 
      d.id === id ? { ...d, status: "updating" as const } : d
    );
    setDeployments(updatingDeployments);

    try {
      // Use Django backend for new deployment
      const deployResult = await blockchainApi.deployRepository(newRepoUrl);
      
      if (deployResult.status === 'deployed') {
        await loadDeployments();
        setUpdatingId(null);
        setNewRepoUrl("");
        toast({
          title: "Repository updated",
          description: "Your deployment has been updated with the new repository.",
        });
      } else {
        // Revert status on failure
        toast({
          title: "Update failed",
          description: deployResult.error || "Failed to update deployment",
          variant: "destructive",
        });
      }
    } catch (error: any) {
      // Revert status on error
      toast({
        title: "Update failed",
        description: error.message || "Network error occurred",
        variant: "destructive",
      });
    }
    await loadDeployments();
  };

  const handleDelete = async (id: string) => {
    toast({
      title: "Delete not available",
      description: "Deployment removal must be performed from the backend or blockchain controller.",
      variant: "destructive",
    });
  };

  const cancelUpdate = () => {
    setUpdatingId(null);
    setNewRepoUrl("");
  };

  const getRepoName = (repoUrl: string): string => {
    try {
      if (!repoUrl || repoUrl === 'Unknown Repository') {
        return '';
      }
      
      // Strip any "repository:" / "system:" style prefixes
      let cleanedRepoUrl = repoUrl
        .replace(/^repository:/i, '')
        .replace(/^system:/i, '')
        .trim();

      // Extract repo name from URL or use the cleaned string directly
      let repoName = cleanedRepoUrl;
      if (cleanedRepoUrl.includes('/')) {
        const parts = cleanedRepoUrl.split('/');
        repoName = parts[parts.length - 1];
      }
      
      // Clean up .git suffix
      return repoName.replace('.git', '');
    } catch (e) {
      return '';
    }
  };

  const getDisplayUrl = (deployment: Deployment) => {
    // Return the actual deployment URL from backend
    return deployment.url;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-zinc-950 via-zinc-900 to-black text-white">
      {/* Glow background accents */}
      <div className="pointer-events-none fixed inset-0 overflow-hidden">
        <div className="absolute -top-24 -left-24 h-64 w-64 rounded-full bg-fuchsia-600/20 blur-3xl" />
        <div className="absolute -bottom-24 -right-24 h-72 w-72 rounded-full bg-indigo-600/20 blur-3xl" />
      </div>

      <header className="relative">
        <div className="mx-auto max-w-6xl px-4 py-8 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link to="/" className="flex items-center gap-3 hover:opacity-80 transition">
              <span className="inline-flex h-9 w-9 items-center justify-center rounded-2xl bg-white/10 backdrop-blur">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
                  <path d="M12 3l7 4v10l-7 4-7-4V7l7-4z" stroke="currentColor" strokeWidth="1.5"/>
                </svg>
              </span>
              <h1 className="text-lg font-semibold tracking-tight">Hacker Tiger</h1>
            </Link>
            <span className="ml-2 rounded-full border border-white/15 px-2 py-0.5 text-[10px] uppercase tracking-wider text-white/70">
              Deployments
            </span>
          </div>
          <Link 
            to="/"
            state={{ activateTestMode: true }}
            className="text-sm text-white/70 hover:text-white transition"
          >
            ← Back to Home
          </Link>
        </div>
      </header>

      <main className="relative mx-auto max-w-6xl px-4 pb-16">
        <div className="mb-8">
          <h2 className="text-2xl font-semibold mb-2">Your Deployments</h2>
          <p className="text-white/70">Manage your blockchain deployments and URLs</p>
        </div>

        {deployments.length === 0 ? (
          <div className="text-center py-16">
            <div className="h-16 w-16 rounded-full bg-white/10 flex items-center justify-center mx-auto mb-4">
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" className="text-white/40">
                <path d="M12 2l8 5v10l-8 5-8-5V7l8-5z" stroke="currentColor" strokeWidth="1.5"/>
              </svg>
            </div>
            <h3 className="text-lg font-medium mb-2">No deployments yet</h3>
            <p className="text-white/60 mb-4">Deploy your first repository to see it here</p>
            <Link 
              to="/"
              state={{ activateTestMode: true }}
              className="inline-flex items-center gap-2 rounded-2xl bg-sky-400 text-black px-4 py-2 text-sm font-medium hover:brightness-95 transition"
            >
              Start Deploying
            </Link>
          </div>
        ) : (
          <div className="space-y-4">
            {deployments.map((deployment) => (
              <div key={deployment.id} className="rounded-3xl border border-white/10 bg-white/5 backdrop-blur p-6">
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                  {/* Repository Info */}
                  <div>
                    <h3 className="font-semibold mb-2">Repository</h3>
                    {updatingId === deployment.id ? (
                      <div className="space-y-3">
                        <input
                          type="url"
                          value={newRepoUrl}
                          onChange={(e) => setNewRepoUrl(e.target.value)}
                          placeholder="https://github.com/owner/repo"
                          className="w-full rounded-xl border border-white/20 bg-white/10 px-3 py-2 text-sm font-mono outline-none focus:ring-2 focus:ring-sky-400/50"
                        />
                        <div className="flex gap-2">
                          <button
                            onClick={() => saveRepoUpdate(deployment.id)}
                            className="rounded-xl bg-emerald-500 px-3 py-1.5 text-xs font-medium text-black hover:brightness-95 transition"
                          >
                            Update & Redeploy
                          </button>
                          <button
                            onClick={cancelUpdate}
                            className="rounded-xl border border-white/20 bg-white/10 px-3 py-1.5 text-xs font-medium text-white/70 hover:text-white transition"
                          >
                            Cancel
                          </button>
                        </div>
                      </div>
                    ) : (
                      <>
                        <div className="flex items-center justify-between mb-2">
                          <p className="text-sm text-sky-400 font-mono break-all">
                            {deployment.repoUrl}
                          </p>
                          <button
                            onClick={() => handleUpdateRepo(deployment.id)}
                            className="ml-2 text-white/40 hover:text-white transition"
                            title="Update Repository"
                          >
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                              <path d="M21 12a9 9 0 0 0-9-9 9.75 9.75 0 0 0-6.74 2.74L3 8" stroke="currentColor" strokeWidth="1.5"/>
                              <path d="M3 3v5h5" stroke="currentColor" strokeWidth="1.5"/>
                              <path d="M3 12a9 9 0 0 0 9 9 9.75 9.75 0 0 0 6.74-2.74L21 16" stroke="currentColor" strokeWidth="1.5"/>
                              <path d="M21 21v-5h-5" stroke="currentColor" strokeWidth="1.5"/>
                            </svg>
                          </button>
                        </div>
                        <p className="text-xs text-white/50">
                          Deployed {new Date(deployment.createdAt).toLocaleDateString()}
                        </p>
                      </>
                    )}
                  </div>

                  {/* Deployment Details */}
                  <div className="lg:col-span-2 space-y-4">
                    {/* Deployment URL */}
                    <div className="rounded-2xl border border-white/10 bg-black/20 p-4">
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" className={`text-orange-400 ${deployment.status === 'updating' ? 'animate-pulse' : ''}`}>
                            <path d="M12 2l8 5v10l-8 5-8-5V7l8-5z" stroke="currentColor" strokeWidth="1.5"/>
                          </svg>
                          <span className="text-sm font-medium">Deployment URL</span>
                        </div>
                        <div className="flex items-center gap-2">
                          {deployment.status === "updating" ? (
                            <div className="h-3 w-3 animate-spin rounded-full border-2 border-sky-400 border-t-transparent"></div>
                          ) : (
                            <div className="relative flex h-2 w-2">
                              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
                            </div>
                          )}
                          <span className={`text-xs font-medium ${deployment.status === "updating" ? "text-sky-400" : "text-emerald-400"}`}>
                            {deployment.status === "updating" ? "Updating..." : "Live"}
                          </span>
                        </div>
                      </div>
                      
                      <a 
                        href={getDisplayUrl(deployment)} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="text-sky-400 font-mono text-sm hover:underline break-all"
                      >
                        {getRepoName(deployment.repoUrl) || getDisplayUrl(deployment)}
                      </a>
                    </div>

                    {/* Blockchain Block ID */}
                    <div className="rounded-2xl border border-white/10 bg-black/20 p-4">
                      <div className="flex items-center gap-2 mb-2">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" className="text-purple-400">
                          <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71" stroke="currentColor" strokeWidth="1.5"/>
                          <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71" stroke="currentColor" strokeWidth="1.5"/>
                        </svg>
                        <span className="text-sm font-medium">Blockchain Block ID</span>
                      </div>
                      <p className="font-mono text-sm text-white/80 break-all">
                        {deployment.blockId}
                      </p>
                      <div className="mt-2 text-xs text-white/50">
                        Block IDs auto-update every 30 seconds
                      </div>
                    </div>

                    {/* Actions */}
                    <div className="flex gap-2 pt-2">
                      <button
                        onClick={() => handleDelete(deployment.id)}
                        className="rounded-2xl border border-red-500/20 bg-red-500/10 px-4 py-2 text-sm font-medium text-red-400 hover:bg-red-500/20 transition"
                      >
                        Delete Deployment
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
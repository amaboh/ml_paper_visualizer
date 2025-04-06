"use client";

import React, { useState, useEffect } from "react";
import { Button, Card, Tabs, Spinner } from "../../../components/ui";
import {
  ArrowLeftIcon,
  DownloadIcon,
  SettingsIcon,
} from "../../../components/icons";
import { useRouter } from "next/navigation";
import SimpleVisualization from "../../../components/SimpleVisualization";

interface ResultsProps {
  params: {
    id: string;
  };
}

interface PaperData {
  id: string;
  title: string;
  status: "uploaded" | "processing" | "completed" | "failed";
  components?: ComponentData[];
  relationships?: RelationshipData[];
}

interface ComponentData {
  id: string;
  type: string;
  name: string;
  description: string;
  source_section: string;
  source_page: number;
  details?: Record<string, unknown>;
}

interface RelationshipData {
  id: string;
  source_id: string;
  target_id: string;
  type: string;
  description: string;
}

export default function Results({ params }: ResultsProps): React.ReactNode {
  const { id } = params;
  const router = useRouter();

  const [paperData, setPaperData] = useState<PaperData | null>(null);
  const [selectedComponent, setSelectedComponent] =
    useState<ComponentData | null>(null);
  const [activeTab, setActiveTab] = useState<string>("details");
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [retryCount, setRetryCount] = useState<number>(0);
  const [pollingTimer, setPollingTimer] = useState<NodeJS.Timeout | null>(null);

  // Cleanup polling on unmount
  useEffect(() => {
    return () => {
      if (pollingTimer) {
        clearInterval(pollingTimer);
      }
    };
  }, [pollingTimer]);

  // Fetch paper data and status
  useEffect(() => {
    const fetchPaperData = async () => {
      try {
        setLoading(true);
        const response = await fetch(`/api/papers/${id}`);

        if (response.status === 404) {
          setError(
            "Paper not found. It may have been deleted or the ID is incorrect."
          );
          setLoading(false);
          return;
        }

        if (!response.ok) {
          throw new Error(`Failed to fetch paper: ${response.statusText}`);
        }

        const data = await response.json();
        setPaperData(data);

        // If completed, stop loading
        if (data.status === "completed") {
          setLoading(false);
        } else if (data.status === "processing") {
          // For processing, we show the visualization with processing state
          // but keep polling for updates
          setLoading(false);

          // Poll for updates if still processing
          const timer = setInterval(async () => {
            try {
              const statusResponse = await fetch(`/api/papers/${id}/status`);
              if (!statusResponse.ok) {
                throw new Error(
                  `Failed to fetch status: ${statusResponse.statusText}`
                );
              }

              const statusData = await statusResponse.json();

              // If status changed, update the paper data
              if (statusData.status !== paperData?.status) {
                // If new status is completed, fetch the full paper data
                if (statusData.status === "completed") {
                  const paperResponse = await fetch(`/api/papers/${id}`);
                  if (paperResponse.ok) {
                    const newPaperData = await paperResponse.json();
                    setPaperData(newPaperData);
                  }
                } else {
                  // Otherwise just update the status
                  setPaperData((prev) =>
                    prev ? { ...prev, status: statusData.status } : null
                  );
                }
              }

              // Stop polling when processing is done
              if (
                statusData.status === "completed" ||
                statusData.status === "failed"
              ) {
                clearInterval(timer);

                if (statusData.status === "failed") {
                  setError(
                    "Paper processing failed. The system couldn't extract ML workflow information."
                  );
                }
              }
            } catch (err) {
              console.error("Error polling paper status:", err);
              // Don't stop polling on temporary errors
            }
          }, 3000); // Poll every 3 seconds

          setPollingTimer(timer);
        } else if (data.status === "uploaded") {
          setError(
            "Paper is waiting to be processed. Please try again in a few moments."
          );
          setLoading(false);
        } else if (data.status === "failed") {
          setError(
            "Paper processing failed. The system couldn't extract ML workflow information."
          );
          setLoading(false);
        }
      } catch (err) {
        console.error("Error fetching paper:", err);
        setError(err instanceof Error ? err.message : "Failed to load paper");
        setLoading(false);
      }
    };

    fetchPaperData();
  }, [id, retryCount]);

  // Function to handle node click in the diagram
  const handleNodeClick = async (nodeId: string) => {
    if (!paperData || !paperData.components) return;

    // Find the component by node ID mapping
    try {
      const response = await fetch(`/api/visualization/${id}/components`);
      if (!response.ok) {
        throw new Error(`Failed to fetch components: ${response.statusText}`);
      }
      const data = await response.json();

      // For now, just select the first component that matches the node name
      // In a real implementation, we would use the component_mapping
      const matchedComponent = data.components.find(
        (c: ComponentData) => c.name.includes(nodeId) || nodeId.includes(c.name)
      );

      if (matchedComponent) {
        setSelectedComponent(matchedComponent);
        setActiveTab("details");
      }
    } catch (err) {
      console.error("Error fetching component details:", err);
    }
  };

  const handleRetry = () => {
    setError(null);
    setRetryCount((prev) => prev + 1);
  };

  const handleBack = () => {
    router.push("/");
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto py-4 px-4 sm:px-6 lg:px-8 flex justify-between items-center">
          <div className="flex items-center">
            <Button
              variant="ghost"
              size="sm"
              leftIcon={<ArrowLeftIcon />}
              onClick={handleBack}
            >
              Back
            </Button>
            <h1 className="ml-4 text-xl font-bold text-gray-900 truncate">
              {paperData?.title || "Loading paper..."}
            </h1>
          </div>
          <div className="flex space-x-2">
            <Button
              variant="outline"
              size="sm"
              leftIcon={<DownloadIcon />}
              disabled={!paperData}
            >
              Export
            </Button>
            <Button
              variant="outline"
              size="sm"
              leftIcon={<SettingsIcon />}
              disabled={!paperData}
            >
              Customize
            </Button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
        {loading ? (
          <div className="flex flex-col items-center justify-center h-64">
            <Spinner size="lg" />
            <p className="mt-4 text-gray-600">Loading paper data...</p>
          </div>
        ) : error ? (
          <div className="bg-red-50 p-8 rounded-md max-w-lg mx-auto text-center">
            <div className="flex flex-col items-center">
              <div className="flex-shrink-0 mb-4">
                <svg
                  className="h-12 w-12 text-red-400"
                  viewBox="0 0 20 20"
                  fill="currentColor"
                >
                  <path
                    fillRule="evenodd"
                    d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                    clipRule="evenodd"
                  />
                </svg>
              </div>
              <h3 className="text-lg font-medium text-red-800 mb-3">Error</h3>
              <div className="text-sm text-red-700 mb-6">
                <p>{error}</p>
              </div>
              <div className="flex space-x-4">
                <Button variant="outline" onClick={handleRetry}>
                  Try Again
                </Button>
                <Button onClick={handleBack}>Return Home</Button>
              </div>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
            {/* Main visualization area */}
            <div className="lg:col-span-3">
              <Card className="h-full">
                <div className="p-4 border-b border-gray-200">
                  <h2 className="text-lg font-medium text-gray-900">
                    ML Workflow Visualization
                  </h2>
                  {paperData?.status === "processing" && (
                    <p className="text-sm text-amber-600 mt-1">
                      Processing paper... This may take a minute.
                    </p>
                  )}
                </div>
                <div
                  className="p-4 overflow-auto"
                  style={{ height: "calc(100vh - 250px)" }}
                >
                  {paperData ? (
                    <SimpleVisualization
                      components={paperData.components || []}
                      relationships={paperData.relationships || []}
                      onNodeClick={handleNodeClick}
                      isProcessing={paperData.status === "processing"}
                    />
                  ) : (
                    <div className="flex items-center justify-center h-full">
                      <p className="text-gray-500">
                        No visualization available
                      </p>
                    </div>
                  )}
                </div>
              </Card>
            </div>

            {/* Sidebar */}
            <div className="lg:col-span-1">
              <Tabs
                tabs={[
                  { id: "details", label: "Component Details" },
                  { id: "paper", label: "Paper Content" },
                ]}
                activeTab={activeTab}
                onChange={setActiveTab}
              />

              <Card className="mt-4">
                {activeTab === "details" ? (
                  selectedComponent ? (
                    <div className="p-4">
                      <h3 className="text-lg font-medium text-gray-900 mb-2">
                        {selectedComponent.name}
                      </h3>
                      <div className="bg-gray-100 px-3 py-1 rounded text-sm text-gray-600 inline-block mb-3">
                        {selectedComponent.type.replace("_", " ")}
                      </div>
                      <p className="text-sm text-gray-600 mb-4">
                        {selectedComponent.description}
                      </p>
                      {selectedComponent.details &&
                        Object.keys(selectedComponent.details).length > 0 && (
                          <div className="bg-gray-50 p-3 rounded-md mb-4">
                            <h4 className="text-sm font-medium text-gray-700 mb-2">
                              Details
                            </h4>
                            <dl className="grid grid-cols-1 gap-x-4 gap-y-2">
                              {Object.entries(selectedComponent.details).map(
                                ([key, value]) => (
                                  <div key={key} className="text-xs">
                                    <dt className="font-medium text-gray-500">
                                      {key}
                                    </dt>
                                    <dd className="text-gray-900">
                                      {JSON.stringify(value)}
                                    </dd>
                                  </div>
                                )
                              )}
                            </dl>
                          </div>
                        )}
                      <div className="mt-3">
                        <p className="text-xs text-gray-500">
                          Source: {selectedComponent.source_section}, Page{" "}
                          {selectedComponent.source_page}
                        </p>
                      </div>
                    </div>
                  ) : (
                    <div className="p-4 text-center text-gray-500">
                      <p>
                        Select a component in the visualization to view details
                      </p>
                    </div>
                  )
                ) : (
                  <div className="p-4">
                    <h3 className="text-lg font-medium text-gray-900 mb-2">
                      Paper Content
                    </h3>
                    <p className="text-sm text-gray-500">
                      This feature is coming soon - you will be able to view the
                      original paper text related to each component.
                    </p>
                  </div>
                )}
              </Card>
            </div>
          </div>
        )}
      </main>

      <footer className="bg-white mt-8">
        <div className="max-w-7xl mx-auto py-4 px-4 sm:px-6 lg:px-8">
          <p className="text-center text-sm text-gray-500">
            ML Paper Visualizer - Version 0.1.0
          </p>
        </div>
      </footer>
    </div>
  );
}

"use client";

import React, { useState } from "react";
import {
  Upload,
  Input,
  Button,
  Card,
  Spinner,
  Alert,
  Tabs,
} from "../components/ui";
import { FileUploadIcon, LinkIcon, ArrowRightIcon } from "../components/icons";
import { useRouter } from "next/navigation";

// Define parser options
const parserOptions = [
  {
    id: "pymupdf",
    label: "PyMuPDF (Standard)",
    description: "Fast, local PDF text extraction.",
  },
  {
    id: "mistral_ocr",
    label: "Mistral OCR (Advanced)",
    description:
      "Cloud-based OCR for complex layouts/scans (requires API key).",
  },
];

export default function Home(): React.ReactNode {
  const router = useRouter();
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>("");
  const [url, setUrl] = useState<string>("");
  const [activeTab, setActiveTab] = useState<string>("upload");
  const [createSampleLoading, setCreateSampleLoading] =
    useState<boolean>(false);
  const [selectedParser, setSelectedParser] = useState<string>(
    parserOptions[0].id
  );

  const handleFileUpload = async (file: File): Promise<void> => {
    setLoading(true);
    setError("");

    try {
      // Create form data
      const formData = new FormData();
      formData.append("file", file);
      formData.append("extractor_type", selectedParser);

      // Send to backend API
      const response = await fetch("/api/papers/upload", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        let errorDetail = `Upload failed: ${response.statusText}`;
        try {
          const errorData = await response.json();
          if (errorData && errorData.detail) {
            errorDetail = `Upload failed: ${errorData.detail}`;
          }
        } catch {
          // Ignore if response is not JSON
        }
        throw new Error(errorDetail);
      }

      const data = await response.json();

      if (data.paper_id) {
        router.push(`/results/${data.paper_id}`);
      } else {
        throw new Error("Processing started, but no paper ID received.");
      }
    } catch (err) {
      setError(
        `Error uploading file: ${
          err instanceof Error ? err.message : "Unknown error"
        }`
      );
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleUrlSubmit = async (
    e: React.FormEvent<HTMLFormElement>
  ): Promise<void> => {
    e.preventDefault();
    if (!url) {
      setError("Please enter a valid URL");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const formData = new FormData();
      formData.append("url", url);
      formData.append("extractor_type", selectedParser);

      const response = await fetch("/api/papers/upload", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        let errorDetail = `Processing URL failed: ${response.statusText}`;
        try {
          const errorData = await response.json();
          if (errorData && errorData.detail) {
            errorDetail = `Processing URL failed: ${errorData.detail}`;
          }
        } catch {
          // Ignore if response is not JSON
        }
        throw new Error(errorDetail);
      }

      const data = await response.json();

      if (data.paper_id) {
        router.push(`/results/${data.paper_id}`);
      } else {
        throw new Error("Processing started, but no paper ID received.");
      }
    } catch (err) {
      setError(
        `Error processing URL: ${
          err instanceof Error ? err.message : "Unknown error"
        }`
      );
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSamplePaper = async (): Promise<void> => {
    setCreateSampleLoading(true);
    setError("");

    try {
      // Call the test endpoint to create a sample paper
      const response = await fetch("/api/papers/test/create-sample", {
        method: "POST",
      });

      if (!response.ok) {
        throw new Error(`Sample creation failed: ${response.statusText}`);
      }

      const data = await response.json();

      // Redirect to results page with the paper ID
      router.push(`/results/${data.id}`);
    } catch (err) {
      setError(
        `Error creating sample paper: ${
          err instanceof Error ? err.message : "Unknown error"
        }`
      );
      console.error(err);
    } finally {
      setCreateSampleLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
          <h1 className="text-3xl font-bold text-gray-900">
            ML Paper Visualizer
          </h1>
        </div>
      </header>

      <main>
        <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
          <div className="px-4 py-6 sm:px-0">
            <div className="max-w-3xl mx-auto">
              <div className="text-center mb-10">
                <h2 className="text-2xl font-semibold text-gray-900">
                  Visualize ML Model Development Process
                </h2>
                <p className="mt-2 text-gray-600">
                  Upload a research paper or provide a URL to visualize the
                  complete ML workflow from data collection to results.
                </p>
              </div>

              <Card className="overflow-hidden">
                <Tabs
                  activeTab={activeTab}
                  onChange={setActiveTab}
                  tabs={[
                    {
                      id: "upload",
                      label: "Upload PDF",
                      icon: <FileUploadIcon />,
                    },
                    { id: "url", label: "Enter URL", icon: <LinkIcon /> },
                  ]}
                />

                <div className="p-6">
                  {error && (
                    <Alert type="error" message={error} className="mb-4" />
                  )}

                  {activeTab === "upload" ? (
                    <Upload
                      accept=".pdf"
                      onChange={handleFileUpload}
                      disabled={loading}
                      placeholder="Drag & drop a PDF file here, or click to browse"
                      className="mb-4"
                    />
                  ) : (
                    <form onSubmit={handleUrlSubmit} className="mb-4">
                      <Input
                        type="url"
                        value={url}
                        onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                          setUrl(e.target.value)
                        }
                        placeholder="https://arxiv.org/pdf/2103.00020.pdf"
                        disabled={loading}
                        className="mb-4"
                      />
                      <Button
                        type="submit"
                        disabled={loading}
                        className="w-full"
                        rightIcon={<ArrowRightIcon />}
                      >
                        {loading ? (
                          <Spinner size="sm" />
                        ) : (
                          "Visualize Paper from URL"
                        )}
                      </Button>
                    </form>
                  )}

                  <div className="mt-4 border-t pt-4">
                    <h4 className="text-sm font-medium text-gray-700 mb-2">
                      PDF Parsing Method:
                    </h4>
                    <div className="space-y-2">
                      {parserOptions.map((option) => (
                        <label
                          key={option.id}
                          className="flex items-center space-x-2 p-2 border rounded-md hover:bg-gray-50 cursor-pointer"
                        >
                          <input
                            type="radio"
                            name="parserType"
                            value={option.id}
                            checked={selectedParser === option.id}
                            onChange={() => setSelectedParser(option.id)}
                            className="form-radio h-4 w-4 text-indigo-600"
                            disabled={loading}
                          />
                          <div>
                            <span className="block text-sm font-medium text-gray-900">
                              {option.label}
                            </span>
                            <span className="block text-xs text-gray-500">
                              {option.description}
                            </span>
                          </div>
                        </label>
                      ))}
                    </div>
                  </div>

                  <div className="mt-6 text-center border-t pt-6">
                    <Button
                      onClick={handleSamplePaper}
                      disabled={createSampleLoading}
                      variant="outline"
                      className="mx-auto"
                    >
                      {createSampleLoading ? (
                        <Spinner size="sm" />
                      ) : (
                        "Try with Sample Paper"
                      )}
                    </Button>
                  </div>
                </div>
              </Card>

              <div className="mt-10">
                <h3 className="text-lg font-medium text-gray-900 mb-4">
                  Example Papers
                </h3>
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                  <Card
                    title="CNN for Image Classification"
                    onClick={() => {
                      setUrl("https://arxiv.org/pdf/1512.03385.pdf");
                      setActiveTab("url");
                    }}
                    className="cursor-pointer hover:shadow-md transition-shadow"
                  >
                    <p className="text-sm text-gray-600">
                      Deep Residual Learning for Image Recognition
                    </p>
                  </Card>
                  <Card
                    title="Transformer Architecture"
                    onClick={() => {
                      setUrl("https://arxiv.org/pdf/1706.03762.pdf");
                      setActiveTab("url");
                    }}
                    className="cursor-pointer hover:shadow-md transition-shadow"
                  >
                    <p className="text-sm text-gray-600">
                      Attention Is All You Need
                    </p>
                  </Card>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>

      <footer className="bg-white">
        <div className="max-w-7xl mx-auto py-6 px-4 overflow-hidden sm:px-6 lg:px-8">
          <p className="text-center text-base text-gray-500">
            ML Paper Visualizer - Version 0.1.0
          </p>
        </div>
      </footer>
    </div>
  );
}

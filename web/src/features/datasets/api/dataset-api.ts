import { ApiClientError, apiErrorSchema, apiRequest } from "@/lib/api-client";
import {
  columnSchema,
  datasetDetailSchema,
  type ColumnInfo,
  type DatasetDetail,
} from "../types/dataset";

export async function uploadDatasetFile(file: File): Promise<DatasetDetail> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch("/api/v1/datasets", {
    method: "POST",
    credentials: "same-origin",
    body: formData,
  });

  if (!response.ok) {
    const raw: unknown = await response.json().catch(() => null);
    const parsed = apiErrorSchema.safeParse(raw);
    throw new ApiClientError(
      response.status,
      parsed.success ? parsed.data.message : `Upload failed with status ${response.status}`,
      parsed.success ? parsed.data : null,
    );
  }

  const data: unknown = await response.json();
  return datasetDetailSchema.parse(data);
}

export function loadSampleDataset(name: string): Promise<DatasetDetail> {
  return apiRequest(`/api/v1/datasets/samples/${encodeURIComponent(name)}`, datasetDetailSchema, {
    method: "POST",
  });
}

export function updateDatasetColumn(
  datasetId: string,
  columnId: string,
  payload: { column_name?: string; pg_type?: string },
): Promise<ColumnInfo> {
  return apiRequest(`/api/v1/datasets/${datasetId}/columns/${columnId}`, columnSchema, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

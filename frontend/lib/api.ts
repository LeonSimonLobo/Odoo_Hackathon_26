const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type ApiError = { detail?: string | { msg: string }[] };

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...init?.headers,
    },
  });

  if (!response.ok) {
    let message = response.statusText;
    try {
      const body = (await response.json()) as ApiError;
      if (typeof body.detail === "string") {
        message = body.detail;
      } else if (Array.isArray(body.detail)) {
        message = body.detail.map((item) => item.msg).join(", ");
      }
    } catch {
      // ignore parse errors
    }
    throw new Error(message);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

export type User = {
  id: number;
  name: string;
  email: string;
  role: string;
  department_id: number | null;
  status: string;
};

export type Category = {
  id: number;
  name: string;
  description: string | null;
};

export type Asset = {
  id: number;
  name: string;
  category_id: number;
  category_name: string | null;
  asset_tag: string;
  serial_number: string | null;
  acquisition_date: string;
  acquisition_cost: number;
  condition: string;
  location: string;
  photo_url: string | null;
  document_url: string | null;
  is_shared: boolean;
  status: string;
  created_at: string;
  updated_at: string;
};

export type AllocationHistory = {
  id: number;
  allocated_to_type: string;
  target: string | null;
  allocation_date: string;
  expected_return_date: string | null;
  actual_return_date: string | null;
  status: string;
};

export type MaintenanceHistory = {
  id: number;
  description: string;
  status: string;
  priority: string;
  technician: string | null;
  created_at: string;
};

export type AssetDetail = Asset & {
  allocation_history: AllocationHistory[];
  maintenance_history: MaintenanceHistory[];
};

export type AssetCreatePayload = {
  name: string;
  category_id: number;
  serial_number?: string;
  acquisition_date: string;
  acquisition_cost: number;
  condition: string;
  location: string;
  photo_url?: string;
  document_url?: string;
  is_shared: boolean;
};

export type AssetSearchParams = {
  search?: string;
  category_id?: number;
  status?: string;
  is_shared?: boolean;
  location?: string;
};

export async function login(email: string, password: string) {
  return apiFetch<{ user: User }>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

export async function getMe() {
  return apiFetch<User>("/auth/me");
}

export async function getCategories() {
  return apiFetch<Category[]>("/api/categories");
}

export async function getAssets(params: AssetSearchParams = {}) {
  const query = new URLSearchParams();
  if (params.search) query.set("search", params.search);
  if (params.category_id != null) query.set("category_id", String(params.category_id));
  if (params.status) query.set("status", params.status);
  if (params.is_shared != null) query.set("is_shared", String(params.is_shared));
  if (params.location) query.set("location", params.location);

  const suffix = query.toString() ? `?${query.toString()}` : "";
  return apiFetch<Asset[]>(`/api/assets${suffix}`);
}

export async function getAsset(id: number) {
  return apiFetch<AssetDetail>(`/api/assets/${id}`);
}

export async function createAsset(payload: AssetCreatePayload) {
  return apiFetch<Asset>("/api/assets", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function formatStatus(status: string) {
  return status
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

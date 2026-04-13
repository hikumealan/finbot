import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/api/client";

interface AuthStatus {
  authenticated: boolean;
  require_pin: boolean;
  has_pin: boolean;
}

export function useAuth() {
  const qc = useQueryClient();

  const status = useQuery<AuthStatus>({
    queryKey: ["auth", "status"],
    queryFn: () => api.get("/api/auth/status"),
    retry: false,
  });

  const login = useMutation({
    mutationFn: (pin: string) => api.post("/api/auth/login", { pin }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["auth"] }),
  });

  const logout = useMutation({
    mutationFn: () => api.post("/api/auth/logout"),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["auth"] }),
  });

  return { status, login, logout };
}

import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useState } from "react";
import { useAuth } from "@/hooks/useAuth";

export const Route = createFileRoute("/login")({
  component: Login,
});

function Login() {
  const [pin, setPin] = useState("");
  const [error, setError] = useState("");
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    try {
      await login.mutateAsync(pin);
      navigate({ to: "/" });
    } catch {
      setError("Incorrect PIN");
    }
  };

  return (
    <div className="flex items-center justify-center min-h-[60vh]">
      <div className="bg-card p-8 rounded-lg border border-border w-full max-w-sm">
        <h1 className="text-2xl font-bold mb-2 text-primary">FinBot</h1>
        <p className="text-muted-foreground mb-6">Enter your PIN to continue</p>
        <form onSubmit={handleSubmit} className="space-y-4">
          <input
            type="password"
            value={pin}
            onChange={(e) => setPin(e.target.value)}
            placeholder="PIN"
            className="w-full px-3 py-2 rounded-md border border-input bg-background"
            autoFocus
          />
          {error && <p className="text-destructive text-sm">{error}</p>}
          <button type="submit" className="w-full bg-primary text-primary-foreground py-2 rounded-md font-medium hover:opacity-90">
            Unlock
          </button>
        </form>
      </div>
    </div>
  );
}

export function useHostedCognitoAuth() {
  return (
    import.meta.env.VITE_USE_COGNITO_AUTH === "true" ||
    (import.meta.env.PROD && import.meta.env.VITE_USE_LOCAL_AUTH !== "true")
  );
}

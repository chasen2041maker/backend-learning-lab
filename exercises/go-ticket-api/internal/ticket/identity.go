package ticket

import (
	"context"
	"net/http"
	"strings"
)

type principalContextKey struct{}

var labTokens = map[string]Principal{
	"lab-token-tenant-a": {Subject: "user_a", TenantID: "tenant_a"},
	"lab-token-tenant-b": {Subject: "user_b", TenantID: "tenant_b"},
}

// Authenticate uses fixed local tokens to teach a trusted identity boundary.
// Production services must verify a signed token or an opaque session and protect
// any identity headers injected by a gateway.
func Authenticate(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		authorization := strings.TrimSpace(r.Header.Get("Authorization"))
		if !strings.HasPrefix(authorization, "Bearer ") {
			writeError(
				w,
				r,
				http.StatusUnauthorized,
				"authentication_required",
				"a bearer token is required",
			)
			return
		}
		principal, ok := labTokens[strings.TrimSpace(strings.TrimPrefix(authorization, "Bearer "))]
		if !ok {
			writeError(
				w,
				r,
				http.StatusUnauthorized,
				"authentication_required",
				"the bearer token is invalid",
			)
			return
		}
		ctx := context.WithValue(r.Context(), principalContextKey{}, principal)
		next.ServeHTTP(w, r.WithContext(ctx))
	})
}

func principalFromContext(ctx context.Context) (Principal, error) {
	principal, ok := ctx.Value(principalContextKey{}).(Principal)
	if !ok {
		return Principal{}, ErrAuthentication
	}
	return principal, nil
}

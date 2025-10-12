from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Dict
import time
import logging

logger = logging.getLogger(__name__)

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory rate limiting middleware."""
    
    def __init__(self, app, max_requests: int = 100, time_window: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.time_window = time_window  # in seconds
        self.request_counts: Dict[str, Dict[str, int]] = {}
    
    def _get_client_id(self, request: Request) -> str:
        """Get client identifier from request."""
        # Try to get client IP
        if request.client:
            return request.client.host
        
        # Fallback to forwarded headers
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        return "unknown"
    
    def _is_rate_limited(self, client_id: str) -> bool:
        """Check if client is rate limited."""
        current_time = int(time.time())
        window_start = current_time - self.time_window
        
        # Clean old entries
        if client_id in self.request_counts:
            self.request_counts[client_id] = {
                timestamp: count 
                for timestamp, count in self.request_counts[client_id].items()
                if int(timestamp) > window_start
            }
        
        # Count requests in current window
        client_requests = self.request_counts.get(client_id, {})
        total_requests = sum(client_requests.values())
        
        return total_requests >= self.max_requests
    
    def _record_request(self, client_id: str):
        """Record a request for the client."""
        current_time = str(int(time.time()))
        
        if client_id not in self.request_counts:
            self.request_counts[client_id] = {}
        
        if current_time not in self.request_counts[client_id]:
            self.request_counts[client_id][current_time] = 0
        
        self.request_counts[client_id][current_time] += 1
    
    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health check and docs
        if request.url.path in ["/health", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)
        
        client_id = self._get_client_id(request)
        
        # Check rate limit
        if self._is_rate_limited(client_id):
            logger.warning(f"Rate limit exceeded for client: {client_id}")
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Please try again later.",
                headers={"Retry-After": str(self.time_window)}
            )
        
        # Record the request
        self._record_request(client_id)
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        client_requests = self.request_counts.get(client_id, {})
        total_requests = sum(client_requests.values())
        remaining = max(0, self.max_requests - total_requests)
        
        response.headers["X-RateLimit-Limit"] = str(self.max_requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(time.time()) + self.time_window)
        
        return response

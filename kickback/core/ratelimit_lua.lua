-- Token bucket rate limiter.
-- KEYS[1] = tokens key
-- KEYS[2] = timestamp key
-- ARGV[1] = capacity
-- ARGV[2] = refill rate per second
-- ARGV[3] = current timestamp
-- ARGV[4] = tokens requested

local tokens_key = KEYS[1]
local timestamp_key = KEYS[2]

local capacity = tonumber(ARGV[1])
local refill_rate = tonumber(ARGV[2])
local now = tonumber(ARGV[3])
local requested = tonumber(ARGV[4])

local tokens = tonumber(redis.call("GET", tokens_key))
if tokens == nil then
  tokens = capacity
end

local last_refill = tonumber(redis.call("GET", timestamp_key))
if last_refill == nil then
  last_refill = now
end

local delta = math.max(0, now - last_refill)
local refill = delta * refill_rate

tokens = math.min(capacity, tokens + refill)
local ttl = math.ceil(capacity / math.max(refill_rate, 0.001))

if tokens < requested then
  redis.call("SET", tokens_key, tokens, "EX", ttl)
  redis.call("SET", timestamp_key, now, "EX", ttl)
  return {0, tokens}
end

tokens = tokens - requested
redis.call("SET", tokens_key, tokens, "EX", ttl)
redis.call("SET", timestamp_key, now, "EX", ttl)

return {1, tokens}

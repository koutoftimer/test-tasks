-- KEYS[1] = v:u:{user_id}
-- KEYS[2] = v:c:{bucket_id}
-- ARGV[1] = comment_id
-- ARGV[2] = new_vote ("1", "-1", "0")

local comment_id = ARGV[1]
local new_vote = ARGV[2]
local prev_vote = redis.call("HGET", KEYS[1], comment_id) or "0"

-- 1. Exit early if there is no change to prevent redundant increments
if prev_vote == new_vote then
    local l = redis.call("HGET", KEYS[2], comment_id .. ":l") or "0"
    local d = redis.call("HGET", KEYS[2], comment_id .. ":d") or "0"
    return {l, d}
end

-- 2. Remove the previous vote's impact from the counter
if prev_vote == "1" then
    redis.call("HINCRBY", KEYS[2], comment_id .. ":l", -1)
elseif prev_vote == "-1" then
    redis.call("HINCRBY", KEYS[2], comment_id .. ":d", -1)
end

-- 3. Apply the new vote
if new_vote == "1" then
    redis.call("HSET", KEYS[1], comment_id, "1")
    redis.call("HINCRBY", KEYS[2], comment_id .. ":l", 1)
elseif new_vote == "-1" then
    redis.call("HSET", KEYS[1], comment_id, "-1")
    redis.call("HINCRBY", KEYS[2], comment_id .. ":d", 1)
else
    -- Use 0 to represent 'Reset' to keep hash clean
    redis.call("HDEL", KEYS[1], comment_id)
end

-- 4. Return current counts so API can respond instantly
local l = redis.call("HGET", KEYS[2], comment_id .. ":l") or "0"
local d = redis.call("HGET", KEYS[2], comment_id .. ":d") or "0"
return {l, d}

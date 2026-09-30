// Loaded after config.js and before app.js.
if (!window.supabase) {
    throw new Error("Supabase JS SDK was not loaded.");
}

if (!SUPABASE_URL || SUPABASE_URL.includes("YOUR_SUPABASE")) {
    throw new Error("Set SUPABASE_URL in config.js");
}

if (!SUPABASE_ANON_KEY || SUPABASE_ANON_KEY.includes("YOUR_SUPABASE")) {
    throw new Error("Set SUPABASE_ANON_KEY in config.js");
}

const supabase = window.supabase.createClient(
    SUPABASE_URL,
    SUPABASE_ANON_KEY
);

window.supabaseClient = supabase;

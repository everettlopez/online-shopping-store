// Everything that identifies the store, from VITE_* variables set at build time
// (see frontend/.env.example). Each store owner sets these instead of editing code.
// vite.config.ts fills in the name when it isn't set.

const env = import.meta.env;

function setting(value: string | undefined): string {
    return value?.trim() ?? "";
}

const name = setting(env.VITE_STORE_NAME) || "Online Store";

export const store = {
    name,
    // The wordmark in the header; defaults to the name in capitals
    logoText: setting(env.VITE_STORE_LOGO_TEXT) || name.toUpperCase(),
    supportEmail: setting(env.VITE_SUPPORT_EMAIL),
    // Shown on the legal and contact pages
    businessName: setting(env.VITE_BUSINESS_NAME) || name,
    businessAddress: setting(env.VITE_BUSINESS_ADDRESS),
    // Whose laws govern the terms, e.g. "Utah"
    businessState: setting(env.VITE_BUSINESS_STATE),
    // Days a customer has to start a return
    returnDays: Number(setting(env.VITE_RETURN_DAYS)) || 30,
    // Owners with their own policies (from a lawyer or a policy service) link to them
    // here; the footer then points there instead of the built-in template pages
    policyUrls: {
        privacy: setting(env.VITE_PRIVACY_POLICY_URL),
        terms: setting(env.VITE_TERMS_URL),
        shipping: setting(env.VITE_SHIPPING_POLICY_URL),
    },
};

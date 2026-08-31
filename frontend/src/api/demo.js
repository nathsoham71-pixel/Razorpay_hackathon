import client from './client'

/**
 * @typedef {Object} DashboardResponse
 * @property {{ id: string, business_name: string, contact_email: string, mcp_access_token: string|null }} merchant
 * @property {{ id: string, version_number: number, status: string, product_count: number }|null} latest_feed
 * @property {number} product_count
 * @property {number} agent_ready_count
 * @property {{ id: string, max_upsell_amount_inr: number, allowed_categories: string[], locked_fields: string[] }|null} active_mandate
 */

/** @returns {Promise<DashboardResponse>} */
export async function getDashboard(merchantId) {
  const { data } = await client.get(`/demo/merchants/${merchantId}/dashboard`)
  return data
}

/**
 * @typedef {Object} FeedUploadResponse
 * @property {Object} feed_version
 * @property {{ raw_row_count: number, valid_count: number, failed_count: number, samples: Array, validation_errors_preview: Array }} before_after_report
 */

/** @returns {Promise<FeedUploadResponse>} */
export async function uploadFeed(merchantId, file) {
  const form = new FormData()
  form.append('file', file)
  const { data } = await client.post(`/merchants/${merchantId}/feed/upload`, form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}

/** @returns {Promise<Array>} */
export async function listProducts(merchantId, isAgentReady = true) {
  const params = {}
  if (typeof isAgentReady === 'boolean') {
    params.is_agent_ready = isAgentReady
  }
  const { data } = await client.get(`/merchants/${merchantId}/products`, { params })
  return data
}

/**
 * @param {string} merchantId
 * @param {{ name?: string, max_upsell_amount_inr: number, allowed_categories: string[], locked_fields: string[] }} body
 */
export async function upsertMandate(merchantId, body) {
  const { data } = await client.post(`/demo/merchants/${merchantId}/mandates`, body)
  return data
}

/**
 * @typedef {Object} PurchaseResponse
 * @property {string} order_id
 * @property {string} razorpay_order_id
 * @property {string} razorpay_key_id
 * @property {number} amount_inr
 * @property {string} status
 */

/** @returns {Promise<PurchaseResponse>} */
export async function simulatePurchase(merchantId, items) {
  const { data } = await client.post(`/demo/merchants/${merchantId}/simulate/purchase`, { items })
  return data
}

/**
 * Upsell chat response shapes (Phase 2 exact):
 * - approved: { reply_text, upsell_status: "approved", new_item, new_total_inr }
 * - rejected: { reply_text, upsell_status: "rejected", rejection_reason, max_allowed_inr }
 * - none: { reply_text, upsell_status: "none_proposed" }
 * Note: backend may also include razorpay_order_id on approved — safe to ignore in UI.
 *
 * @returns {Promise<Object>}
 */
export async function simulateUpsellChat(orderId, buyerMessage, conversationHistory = []) {
  const { data } = await client.post(`/demo/orders/${orderId}/simulate/upsell-chat`, {
    buyer_message: buyerMessage,
    conversation_history: conversationHistory,
  })
  return data
}

/** @returns {Promise<Object>} */
export async function confirmPurchase(orderId, razorpayPaymentId, razorpaySignature) {
  const { data } = await client.post(`/demo/orders/${orderId}/confirm`, {
    razorpay_payment_id: razorpayPaymentId,
    razorpay_signature: razorpaySignature,
  })
  return data
}

/** @returns {Promise<Object>} */
export async function createMerchant(businessName, contactEmail) {
  const { data } = await client.post('/merchants', {
    business_name: businessName,
    contact_email: contactEmail,
  })
  return data
}

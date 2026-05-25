const { makeWASocket, useMultiFileAuthState, DisconnectReason } = require('@whiskeysockets/baileys');
const axios = require('axios');
const qrcode = require('qrcode-terminal');

const OWNER_NUMBER = '92300XXXXXXX@s.whatsapp.net'; // <--- APNA NUMBER YAHAN LIKHEIN

async function connectToWhatsApp() {
    const { state, saveCreds } = await useMultiFileAuthState('auth_info_baileys');
    const sock = makeWASocket({ auth: state });

    sock.ev.on('creds.update', saveCreds);
    sock.ev.on('connection.update', (update) => {
        const { qr, connection } = update;
        if (qr) qrcode.generate(qr, { small: true });
        if (connection === 'open') console.log('✅ Bot Connected!');
    });

    sock.ev.on('messages.upsert', async ({ messages, type }) => {
        if (type !== 'notify') return;
        const msg = messages[0];
        if (!msg.message || msg.key.fromMe) return;

        const jid = msg.key.remoteJid;
        const text = msg.message.conversation || msg.message.extendedTextMessage?.text;

        try {
            const response = await axios.post('http://127.0.0.1:8001/chat', {
                user_input: text,
                sender_id: jid
            });

            const data = response.data;

            // 1. Agar Order hai to Owner ko notify karo
            if (data.is_order) {
                await sock.sendMessage(OWNER_NUMBER, { text: "🔔 *New Order Received!*\n\n" + data.reply });
            }

            // 2. Customer ko response bhejo
            if (data.type === 'text_image' && data.image_url) {
                const imgRes = await axios.get(data.image_url, { responseType: 'arraybuffer' });
                await sock.sendMessage(jid, { 
                    image: Buffer.from(imgRes.data), 
                    caption: data.reply 
                }, { linkPreview: false }); 
            } else {
                await sock.sendMessage(jid, { text: data.reply }, { linkPreview: false });
            }
        } catch (error) {
            console.error("❌ Error:", error.message);
        }
    });
}
connectToWhatsApp();
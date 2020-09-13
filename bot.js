const Discord = require("discord.js");
const client = new Discord.Client();
const token = process.env.BOT_TOKEN

client.on("ready", () => {
  console.log(`Logged in as ${client.user.tag}!`);
});

client.on("message", msg => {
  if (msg.content.startsWith("p?")) {
    msg.reply("pong");
  }
});

client.login(token);
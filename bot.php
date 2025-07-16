<?php
require_once 'config.php';

// Function to send API requests to Telegram using cURL
function sendRequest($bot_token, $method, $params = []) {
    $url = 'https://api.telegram.org/bot' . $bot_token . '/' . $method;
    
    $ch = curl_init();
    curl_setopt($ch, CURLOPT_URL, $url);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_POST, true);
    curl_setopt($ch, CURLOPT_POSTFIELDS, $params);
    curl_setopt($ch, CURLOPT_TIMEOUT, 1); // Set timeout to 1 second
    curl_setopt($ch, CURLOPT_CONNECTTIMEOUT, 1); // Set connection timeout to 1 second
    
    $result = curl_exec($ch);
    curl_close($ch);
    return $result;
}

// Function to add reaction to a message
function addReaction($bot_token, $chat_id, $message_id, $reaction) {
    $params = [
        'chat_id' => $chat_id,
        'message_id' => $message_id,
        'reaction' => json_encode([['type' => 'emoji', 'emoji' => $reaction]])
    ];
    return sendRequest($bot_token, 'setMessageReaction', $params);
}

// Get updates from Telegram
$update = json_decode(file_get_contents('php://input'), true);

// Check if it's a new message or channel post
if (isset($update['message']) || isset($update['channel_post'])) {
    // Get message data from either regular message or channel post
    $message = isset($update['message']) ? $update['message'] : $update['channel_post'];
    $chat_id = $message['chat']['id'];
    $message_id = $message['message_id'];
    
    // Get random reaction from the array
    global $reactions;
    $random_reaction = $reactions[array_rand($reactions)];
    
    // Add reactions from all bots using async requests
    global $bot_tokens;
    $mh = curl_multi_init();
    $handles = [];
    
    foreach ($bot_tokens as $token_name => $bot_token) {
        $ch = curl_init();
        $url = 'https://api.telegram.org/bot' . $bot_token . '/setMessageReaction';
        $params = [
            'chat_id' => $chat_id,
            'message_id' => $message_id,
            'reaction' => json_encode([['type' => 'emoji', 'emoji' => $random_reaction]])
        ];
        
        curl_setopt($ch, CURLOPT_URL, $url);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($ch, CURLOPT_POST, true);
        curl_setopt($ch, CURLOPT_POSTFIELDS, $params);
        curl_setopt($ch, CURLOPT_TIMEOUT, 1);
        curl_setopt($ch, CURLOPT_CONNECTTIMEOUT, 1);
        
        curl_multi_add_handle($mh, $ch);
        $handles[$token_name] = $ch;
    }
    
    // Execute all requests in parallel
    $running = null;
    do {
        curl_multi_exec($mh, $running);
    } while ($running);
    
    // Close all handles
    foreach ($handles as $token_name => $ch) {
        $result = curl_multi_getcontent($ch);
        error_log("Reaction attempt from $token_name for message $message_id in chat $chat_id: " . $result);
        curl_multi_remove_handle($mh, $ch);
    }
    
    curl_multi_close($mh);
}
?>
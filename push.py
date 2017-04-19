import pusher

pusher_client = pusher.Pusher("329265", "bdf3e36a58647e366f38", "a631bb96bd8a4b3c0e69")

pusher_client.notify(['polls'], {
  'fcm': {
    'registration_ids': ['frqhK8oWOVc:APA91bGhIS6wNMgxaJXl8ioVBUODCDBQtIQBXTSSLStOm-apMnyno9YhaxQZIeDywzyyWZfMSx86uX7RcinT8Z_4AOpssPNchP_AIDsGAhWT6RkmZM-9_hmPmzsKKVZIrViNrDpaHwFV'],
    'notification': {
      'title': 'hello world 2',
      'body': 'whats up doc?'
    }
  },
  'webhook_url': 'http://requestb.in/1f7u53z1',
  'webhook_level': 'DEBUG'
})

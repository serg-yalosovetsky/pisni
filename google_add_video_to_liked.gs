function addLikedVideosToPlaylist(skipCount = 2050) {
  var playlistId = 'PLEJYPrcLjkrViJpaliSuODRtJC0ILQzSA';
  
  var nextPageToken = '';
  var processedCount = 0;
  
  // Получаем все видео, уже находящиеся в плейлисте
  var existingVideos = getExistingVideos(playlistId);
  
  do {
    var likedVideos = YouTube.Videos.list('snippet', {
      myRating: 'like',
      maxResults: 50,
      pageToken: nextPageToken
    });
    
    for (var i = 0; i < likedVideos.items.length; i++) {
      processedCount++;
      
      if (processedCount <= skipCount) {
        continue;
      }
      
      var videoId = likedVideos.items[i].id;
      
      // Проверяем, есть ли видео уже в плейлисте
      if (!existingVideos.includes(videoId)) {
        try {
          YouTube.PlaylistItems.insert(
            {
              snippet: {
                playlistId: playlistId,
                resourceId: {
                  kind: 'youtube#video',
                  videoId: videoId
                }
              }
            },
            'snippet'
          );
          
          Logger.log('Добавлено видео #' + processedCount + ': ' + videoId);
        } catch (e) {
          Logger.log('Ошибка при добавлении видео ' + videoId + ': ' + e.message);
        }
      } else {
        Logger.log('Видео ' + videoId + ' уже существует в плейлисте');
      }
    }
    
    nextPageToken = likedVideos.nextPageToken;
  } while (nextPageToken);
  
  Logger.log('Всего обработано видео: ' + processedCount);
}

// Функция для получения всех видео, уже находящихся в плейлисте
function getExistingVideos(playlistId) {
  var existingVideos = [];
  var nextPageToken = '';
  
  do {
    var playlistItems = YouTube.PlaylistItems.list('snippet', {
      playlistId: playlistId,
      maxResults: 50,
      pageToken: nextPageToken
    });
    
    for (var i = 0; i < playlistItems.items.length; i++) {
      existingVideos.push(playlistItems.items[i].snippet.resourceId.videoId);
    }
    
    nextPageToken = playlistItems.nextPageToken;
  } while (nextPageToken);
  
  return existingVideos;
}

function removeDuplicatesFromPlaylist(playlistId) {
  var existingVideos = {};
  var itemsToDelete = [];
  var nextPageToken = '';
  
  do {
    var playlistItems = YouTube.PlaylistItems.list('snippet', {
      playlistId: playlistId,
      maxResults: 50,
      pageToken: nextPageToken
    });
    
    for (var i = 0; i < playlistItems.items.length; i++) {
      var item = playlistItems.items[i];
      var videoId = item.snippet.resourceId.videoId;
      
      if (existingVideos[videoId]) {
        // Это дубликат, добавляем его ID в список для удаления
        itemsToDelete.push(item.id);
      } else {
        // Это первое появление видео, отмечаем его как существующее
        existingVideos[videoId] = true;
      }
    }
    
    nextPageToken = playlistItems.nextPageToken;
  } while (nextPageToken);
  
  // Удаляем дубликаты
  for (var j = 0; j < itemsToDelete.length; j++) {
    try {
      YouTube.PlaylistItems.remove(itemsToDelete[j]);
      Logger.log('Удален дубликат: ' + itemsToDelete[j]);
    } catch (e) {
      Logger.log('Ошибка при удалении дубликата ' + itemsToDelete[j] + ': ' + e.message);
    }
  }
  
  Logger.log('Всего удалено дубликатов: ' + itemsToDelete.length);
}

// Пример использования:
// var playlistId = 'PLEJYPrcLjkrViJpaliSuODRtJC0ILQzSA';
// removeDuplicatesFromPlaylist(playlistId);
// addLikedVideosToPlaylist(200);  // Пропустить первые 200 видео
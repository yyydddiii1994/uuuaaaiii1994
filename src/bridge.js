// src/bridge.js

document.addEventListener('DOMContentLoaded', () => {
    // QWebChannelの初期化を試行
    if (typeof qt === 'undefined' || typeof qt.webChannelTransport === 'undefined') {
        console.error("QWebChannel is not available. Make sure qwebchannel.js is loaded.");
        return;
    }

    new QWebChannel(qt.webChannelTransport, (channel) => {
        // Python側で'backend'という名前で公開されたオブジェクトを取得
        const backend = channel.objects.backend;

        if (!backend) {
            console.error("Backend object not found in QWebChannel.");
            return;
        }

        let currentSelectedId = null;

        // ドキュメント全体のクリックイベントを捕捉
        document.body.addEventListener('click', (event) => {
            // イベントの伝播を停止し、デフォルトの動作（リンク遷移など）を防ぐ
            event.preventDefault();
            event.stopPropagation();

            const target = event.target;

            // クリックされた要素またはその祖先から data-element-id を持つ要素を探す
            const elementWithId = target.closest('[data-element-id]');

            if (elementWithId) {
                const elementId = elementWithId.getAttribute('data-element-id');

                // Python側に要素IDを通知
                backend.onElementClicked(elementId);
            }
        });

        // --- Python側から呼び出されるグローバル関数を定義 ---
        window.highlightElement = (elementId) => {
            // 以前に選択されていた要素からハイライトクラスを削除
            if (currentSelectedId) {
                const oldSelected = document.querySelector(`[data-element-id="${currentSelectedId}"]`);
                if (oldSelected) {
                    oldSelected.classList.remove('selected-element');
                }
            }

            // 新しい要素をハイライト
            const newSelected = document.querySelector(`[data-element-id="${elementId}"]`);
            if (newSelected) {
                newSelected.classList.add('selected-element');
                currentSelectedId = elementId;
            } else {
                currentSelectedId = null;
            }
        };

        console.log("Bridge setup complete. Ready to communicate.");
    });
});

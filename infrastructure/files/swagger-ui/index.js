window.onload = function() {
    // Begin Swagger UI call region
    window.ui = SwaggerUIBundle({
        url: "swagger.yaml",
        dom_id: '#swagger-ui',
        deepLinking: true,
        presets: [
            SwaggerUIBundle.presets.apis,
            SwaggerUIStandalonePreset
        ],
        plugins: [
            SwaggerUIBundle.plugins.DownloadUrl
        ],
        layout: "StandaloneLayout"
    });
    // End Swagger UI call region

};
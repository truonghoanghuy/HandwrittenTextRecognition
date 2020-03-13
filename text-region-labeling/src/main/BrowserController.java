package main;

import javafx.fxml.FXML;
import javafx.fxml.FXMLLoader;
import javafx.scene.Parent;
import javafx.scene.Scene;
import javafx.scene.control.Button;
import javafx.scene.control.TextField;
import javafx.scene.image.Image;
import javafx.stage.FileChooser;
import javafx.stage.FileChooser.ExtensionFilter;
import javafx.stage.Stage;

import javax.annotation.PostConstruct;
import java.io.File;
import java.util.List;

public class BrowserController {

    private static ExtensionFilter textFilter = new ExtensionFilter("Text files", "*.txt");
    private static ExtensionFilter imageFilter = new ExtensionFilter("Image files", "*.jpg", "*.png");

    @FXML
    public Button browseImageBtn;
    @FXML
    public TextField outputFileName;
    @FXML
    public Button browseTextBtn;

    private Stage ownerStage;
    private File outputFile;

    @PostConstruct
    public void initialize() {
        browseTextBtn.setOnAction(event -> openTextFileBrowser());
        browseImageBtn.setOnAction(event -> openImageFileBrowser());
    }

    public void openTextFileBrowser() {
        FileChooser fileChooser = new FileChooser();
        fileChooser.getExtensionFilters().setAll(textFilter);
        File file = fileChooser.showOpenDialog(ownerStage);
        if (file != null) {
            outputFile = file;
            outputFileName.setText(file.toString());
        }
    }

    private void openImageFileBrowser() {
        FileChooser fileChooser = new FileChooser();
        fileChooser.getExtensionFilters().setAll(imageFilter);
        List<File> files = fileChooser.showOpenMultipleDialog(ownerStage);
        if (files != null) {
            files.forEach(this::openViewerStage);
        }
    }

    private void openViewerStage(File file) {
        try {

            Image image = new Image(file.toURI().toURL().toExternalForm());
            FXMLLoader fxmlLoader = new FXMLLoader(getClass().getResource("viewer.fxml"));
            Parent loader = fxmlLoader.load();
            ViewerController viewerController = fxmlLoader.getController();
            viewerController.setOriginalImage(image, file.getName());
            viewerController.setBrowserController(this);

            Stage viewerStage = new Stage();
            viewerStage.setTitle("Viewer");
            viewerStage.setMinHeight(300);
            viewerStage.setMinWidth(400);
            viewerStage.setScene(new Scene(loader, 600, 600));
            viewerStage.show();

        } catch (Exception e) {
            App.showExceptionAlert(e);
        }
    }

    public File getOutputFile() {
        return outputFile;
    }

    public void setOwnerStage(Stage ownerStage) {
        this.ownerStage = ownerStage;
    }
}
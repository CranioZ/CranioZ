Responsável pela importação e manipulação de volumes, sejam em formato DICOM ou não. 

## Funcionalidades
* Leitura de séries DICOM e VTI; 
* Reconstrução volumétrica; 
* Window/Level (Ajuste do brilho e contraste das janelas 2D); 
* Reslice 
* MIP / MinIP 
* Monitoramento do consumo de memória;
* Gerenciamento de grandes volumes; 
* Processamento assíncrono com múltiplas threads; 

## Editors
* Visualização multiplanar (MPR) com renderização volumétrica (Visualização 3d do volume da TC); 
* Curved MPR (Reconstrução panorâmica);

## Tools
* Criar plano com imagens 2D da MPR da TC (axial, coronal ou sagital) sincronizada na view 3D.
* Presets de renderização 3D.
* Color Lookup Tables (LUTs); 
* Exportação de arquivos volume (.vti); 

## Simplicidade visual
Para evitar a poluição visual e foco nas imagens e não nas ferramentas os editores de DICOM não vão exibir ferramentas (tools) por padrão. A exibição será condicionada a presença do mouse no editor. Se o mouse não estiver no editor as ferramentas e o ícone de marca o tipo de corte (axial, coronal, sagital) ficarão semi ocultos. Quando o mouse mover para o editor estes elementos se tornarão totalmente visíveis. 